"""
Mixins for reusable logic in members views to reduce code duplication
"""
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from django.core.paginator import Paginator
import csv
import io

from ..models import CustomUser, NewFriend, RegularMember, Group, Role, ActivityLog


class MemberFilterMixin:
    """Mixin for common member filtering logic"""
    
    def filter_members_by_search(self, members, search_term):
        """Filter members by search term"""
        if search_term:
            return members.filter(
                Q(first_name__icontains=search_term) |
                Q(last_name__icontains=search_term) |
                Q(email__icontains=search_term) |
                Q(phone_number__icontains=search_term)
            )
        return members
    
    def filter_members_by_role(self, members, role_filter):
        """Filter members by role"""
        if role_filter:
            return members.filter(role__name=role_filter)
        return members
    
    def filter_members_by_status(self, members, status_filter):
        """Filter members by new friend/regular status"""
        if status_filter == 'new_friends':
            return members.filter(is_new_friend=True)
        elif status_filter == 'regular_members':
            return members.filter(is_new_friend=False)
        return members


class PaginationMixin:
    """Mixin for pagination logic"""
    
    def paginate_queryset(self, queryset, request, per_page=10):
        """Paginate a queryset"""
        paginator = Paginator(queryset, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return page_obj


class NewFriendMixin:
    """Mixin for new friend related operations"""
    
    def get_new_friends_for_church(self, church):
        """Get all new friends for a church"""
        return CustomUser.objects.filter(
            church=church,
            is_active=True,
            is_new_friend=True
        )
    
    def filter_new_friends_by_timer_status(self, new_friends, timer_status):
        """Filter new friends by timer status"""
        if timer_status:
            return new_friends.filter(timer_status=timer_status)
        return new_friends
    
    def filter_new_friends_by_follow_up(self, new_friend_profiles, follow_up_status):
        """Filter new friend profiles by follow up status"""
        if follow_up_status:
            return [nf for nf in new_friend_profiles if nf.follow_up_status == follow_up_status]
        return new_friend_profiles
    
    def create_new_friend_user(self, form_data, church):
        """Create a new friend user with default settings"""
        default_password = f"jcsgo{church.domain}"
        
        user = CustomUser.objects.create_user(
            email=form_data['full_email'],
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            phone_number=form_data.get('phone'),
            church=church,
            is_new_friend=True,
            is_active=True,
            password=default_password
        )
        
        user.timer_status = form_data.get('timer_status', 1)
        user.save()
        
        return user


class RegularMemberMixin:
    """Mixin for regular member related operations"""
    
    def get_regular_members_for_church(self, church):
        """Get all regular members for a church"""
        return CustomUser.objects.filter(
            church=church,
            is_active=True,
            is_new_friend=False
        )
    
    def filter_regular_members_by_group(self, regular_members, group_filter):
        """Filter regular members by group"""
        if group_filter:
            return regular_members.filter(
                regular_member_profile__group__name__icontains=group_filter
            )
        return regular_members
    
    def create_regular_member_user(self, form_data, church):
        """Create a regular member user with default settings"""
        default_password = f"jcsgo{church.domain}"
        
        user = CustomUser.objects.create_user(
            email=form_data['full_email'],
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            phone_number=form_data.get('phone'),
            church=church,
            is_new_friend=False,
            is_active=True,
            password=default_password
        )
        
        user.role = form_data['role']
        user.save()
        
        return user


class GroupMixin:
    """Mixin for group related operations"""
    
    def get_groups_for_church(self, church, group_type=None):
        """Get groups for a church, optionally filtered by type"""
        groups = Group.objects.filter(
            church=church,
            is_active=True
        ).select_related('leader').prefetch_related('members')
        
        if group_type:
            groups = groups.filter(group_type=group_type)
            
        return groups
    
    def filter_groups_by_search(self, groups, search_term):
        """Filter groups by search term"""
        if search_term:
            return groups.filter(
                Q(name__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(leader__first_name__icontains=search_term) |
                Q(leader__last_name__icontains=search_term)
            )
        return groups
    
    def get_group_statistics(self, groups):
        """Get statistics for groups"""
        return {
            'total_groups': groups.count(),
            'care_groups_count': groups.filter(group_type='CARE').count(),
            'ministry_groups_count': groups.filter(group_type='MINISTRY').count(),
        }


class ActivityLogMixin:
    """Mixin for activity log operations"""
    
    def get_activities_for_church(self, church):
        """Get activities for a church"""
        return ActivityLog.objects.filter(
            church=church
        ).select_related('user', 'related_user').order_by('-timestamp')
    
    def filter_activities(self, activities, filters):
        """Filter activities by various criteria"""
        if filters.get('action'):
            activities = activities.filter(action=filters['action'])
        
        if filters.get('user'):
            activities = activities.filter(user__id=filters['user'])
        
        if filters.get('date_from'):
            activities = activities.filter(timestamp__date__gte=filters['date_from'])
        
        if filters.get('date_to'):
            activities = activities.filter(timestamp__date__lte=filters['date_to'])
        
        return activities
    
    def create_activity_log(self, user, action, description, request, related_user=None):
        """Create an activity log entry"""
        ActivityLog.objects.create(
            user=user,
            action=action,
            description=description,
            related_user=related_user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )


class ImportMixin:
    """Mixin for CSV import operations"""
    
    def process_csv_file(self, file):
        """Process a CSV file and return data"""
        decoded_file = file.read().decode('utf-8')
        return csv.DictReader(io.StringIO(decoded_file))
    
    def import_new_friends_from_csv(self, csv_data, church, user):
        """Import new friends from CSV data"""
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_data, start=2):
            try:
                # Process new friend import logic here
                imported_count += 1
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return imported_count, errors
    
    def import_regular_members_from_csv(self, csv_data, church, user):
        """Import regular members from CSV data"""
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_data, start=2):
            try:
                # Process regular member import logic here
                imported_count += 1
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        return imported_count, errors


class PermissionMixin:
    """Mixin for permission checking"""
    
    def check_admin_permission(self, user):
        """Check if user has admin permission"""
        return user.is_superuser or user.role.name == 'ADMIN'
    
    def check_leadership_permission(self, user):
        """Check if user has leadership permission (VSL, CSL, CL, ADMIN)"""
        return user.role.name in ['VSL', 'CSL', 'CL', 'ADMIN'] or user.is_superuser
    
    def check_church_access(self, user, church):
        """Check if user can access church data"""
        return user.can_access_church_data(church)
    
    def filter_groups_by_role(self, groups, user):
        """Filter groups based on user role permissions"""
        if user.role.name == 'VSL':
            # VSL can see their groups and subordinate groups
            user_groups = Group.objects.filter(leader=user, group_type='CARE')
            member_users = CustomUser.objects.filter(
                regular_member_profile__group__in=user_groups
            ).exclude(id=user.id)
            
            return groups.filter(
                Q(leader=user) | 
                Q(leader__in=member_users)
            ).distinct()
            
        elif user.role.name == 'CSL':
            # CSL can see their groups and subordinate groups
            user_groups = Group.objects.filter(leader=user, group_type='CARE')
            member_users = CustomUser.objects.filter(
                regular_member_profile__group__in=user_groups
            ).exclude(id=user.id)
            
            return groups.filter(
                Q(leader=user) | 
                Q(leader__in=member_users)
            ).distinct()
            
        elif user.role.name == 'CL':
            # CL can only see their own groups
            return groups.filter(leader=user)
            
        elif user.role.name == 'ADMIN' or user.is_superuser:
            # Admin can see all groups
            return groups
            
        else:
            # Regular members can't see care groups management
            return groups.none()


class RoleManagementMixin:
    """Mixin for role management operations"""
    
    def get_available_roles(self):
        """Get available roles for assignment"""
        return Role.objects.filter(
            name__in=['VSL', 'CSL', 'CL', 'CM']
        ).order_by('name')
    
    def promote_user_role(self, endorsed_to_user, request_user, request):
        """Promote user from CM to CL when they get a new friend endorsement"""
        if endorsed_to_user and endorsed_to_user.role and endorsed_to_user.role.name == 'CM':
            cl_role = Role.objects.get(name='CL')
            endorsed_to_user.role = cl_role
            endorsed_to_user.save()
            
            if hasattr(endorsed_to_user, 'regular_member_profile') and endorsed_to_user.regular_member_profile:
                endorsed_to_user.regular_member_profile.role_type = 'CL'
                endorsed_to_user.regular_member_profile.save()

            self.create_activity_log(
                request_user,
                'ROLE_PROMOTED',
                f'Promoted {endorsed_to_user.full_name} from CM to CL due to new friend endorsement',
                request,
                endorsed_to_user
            )
            
            return True
        return False
    
    def transition_new_friend_to_regular(self, user, role_name, request_user, request):
        """Transition a new friend to regular member"""
        user.is_new_friend = False
        user.transition_date = timezone.now()
        role = Role.objects.get(name=role_name)
        user.role = role
        user.save()

        RegularMember.objects.get_or_create(
            user=user,
            defaults={'role_type': role_name}
        )

        # Remove new friend profile
        try:
            if hasattr(user, 'new_friend_profile'):
                user.new_friend_profile.delete()
        except NewFriend.DoesNotExist:
            pass

        self.create_activity_log(
            request_user,
            'STATUS_CHANGE',
            f'Transitioned {user.full_name} from New Friend to Regular Member',
            request,
            user
        )
