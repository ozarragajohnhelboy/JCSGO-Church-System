"""Keep care group reports and Attendance records in sync.

Leaders record Care Group and Sunday presence on weekly reports and on the
care group tracker. Other event types stay on the admin/QR scanner.
"""
from datetime import timedelta

from django.db.models import Max
from django.utils import timezone

from ..models import Attendance, CareGroupMemberReport, CareGroupReport

SOURCE_NOTE_PREFIX = 'Care group:'


def sunday_on_or_before(day):
    """Return the Sunday on or before `day` (the Sunday of that ministry week)."""
    return day - timedelta(days=(day.weekday() + 1) % 7)


def _source_note(group_name):
    return f'{SOURCE_NOTE_PREFIX} {group_name}'


def _is_leader_sourced(attendance):
    return (attendance.notes or '').startswith(SOURCE_NOTE_PREFIX)


def apply_attendance(member, church, date, attendance_type, present, recorded_by, group_name):
    """Create or remove a leader-sourced attendance row without touching QR scans.

    Returns True when the member remains present afterward (including QR scans
    that leaders cannot clear from this screen).
    """
    lookup = {
        'user': member,
        'date': date,
        'attendance_type': attendance_type,
    }
    existing = Attendance.objects.filter(**lookup).first()

    if present:
        if existing:
            return True
        Attendance.objects.create(
            **lookup,
            church=church,
            time_in=timezone.localtime().time(),
            scanned_by=recorded_by,
            notes=_source_note(group_name),
        )
        member.record_attendance()
        return True

    if existing and _is_leader_sourced(existing):
        existing.delete()
        return False
    return bool(existing)


def sync_report_member_attendance(report, recorded_by):
    """Write Attendance rows from a saved care group report."""
    sunday_date = sunday_on_or_before(report.date_of_cg)
    group_name = report.care_group.name
    church = report.church

    for member_report in report.member_reports.select_related('member'):
        apply_attendance(
            member=member_report.member,
            church=church,
            date=report.date_of_cg,
            attendance_type='CARE_GROUP',
            present=member_report.group_attendance,
            recorded_by=recorded_by,
            group_name=group_name,
        )
        apply_attendance(
            member=member_report.member,
            church=church,
            date=sunday_date,
            attendance_type='SUNDAY',
            present=member_report.sunday_attendance,
            recorded_by=recorded_by,
            group_name=group_name,
        )


def _week_report_ids_for_sunday(care_group, sunday_date):
    reports = CareGroupReport.objects.filter(
        care_group=care_group,
        date_of_cg__gte=sunday_date,
        date_of_cg__lt=sunday_date + timedelta(days=7),
    )
    return [report.id for report in reports if sunday_on_or_before(report.date_of_cg) == sunday_date]


def present_member_ids(care_group, members, selected_date):
    """Member IDs present for Care Group and Sunday on `selected_date`.

    A member is present if an Attendance row exists that day, or a matching
    care group report already marked them present.
    """
    member_ids = [member.id for member in members]
    if not member_ids:
        return set(), set()

    care_group_ids = set(
        Attendance.objects.filter(
            user_id__in=member_ids,
            date=selected_date,
            attendance_type='CARE_GROUP',
        ).values_list('user_id', flat=True)
    )
    sunday_ids = set(
        Attendance.objects.filter(
            user_id__in=member_ids,
            date=selected_date,
            attendance_type='SUNDAY',
        ).values_list('user_id', flat=True)
    )

    care_group_ids |= set(
        CareGroupMemberReport.objects.filter(
            report__care_group=care_group,
            report__date_of_cg=selected_date,
            group_attendance=True,
            member_id__in=member_ids,
        ).values_list('member_id', flat=True)
    )

    sunday_report_ids = _week_report_ids_for_sunday(care_group, selected_date)
    if sunday_report_ids:
        sunday_ids |= set(
            CareGroupMemberReport.objects.filter(
                report_id__in=sunday_report_ids,
                sunday_attendance=True,
                member_id__in=member_ids,
            ).values_list('member_id', flat=True)
        )

    return care_group_ids, sunday_ids


def last_attendance_dates(members):
    rows = Attendance.objects.filter(
        user__in=members,
        attendance_type__in=('CARE_GROUP', 'SUNDAY'),
    ).values('user_id').annotate(last_date=Max('date'))
    return {row['user_id']: row['last_date'] for row in rows}


def save_tracker_attendance(care_group, members, selected_date, recorded_by, care_group_present_ids, sunday_present_ids):
    """Save tracker checkboxes and mirror them onto any matching weekly report."""
    group_name = care_group.name
    church = care_group.church
    sunday_report_ids = _week_report_ids_for_sunday(care_group, selected_date)
    care_group_count = 0
    sunday_count = 0

    for member in members:
        care_group_present = apply_attendance(
            member=member,
            church=church,
            date=selected_date,
            attendance_type='CARE_GROUP',
            present=member.id in care_group_present_ids,
            recorded_by=recorded_by,
            group_name=group_name,
        )
        sunday_present = apply_attendance(
            member=member,
            church=church,
            date=selected_date,
            attendance_type='SUNDAY',
            present=member.id in sunday_present_ids,
            recorded_by=recorded_by,
            group_name=group_name,
        )
        if care_group_present:
            care_group_count += 1
        if sunday_present:
            sunday_count += 1

        CareGroupMemberReport.objects.filter(
            report__care_group=care_group,
            report__date_of_cg=selected_date,
            member=member,
        ).update(group_attendance=care_group_present)

        if sunday_report_ids:
            CareGroupMemberReport.objects.filter(
                report_id__in=sunday_report_ids,
                member=member,
            ).update(sunday_attendance=sunday_present)

    return care_group_count, sunday_count
