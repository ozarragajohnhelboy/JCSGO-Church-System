"""
Mixins for reusable dashboard logic to reduce code duplication
"""
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count

from members.models import Church, Role, CustomUser, ActivityLog


class ChurchStatsMixin:
    """Mixin for common church statistics"""
    
    def get_church_member_counts(self, church):
        """Get basic member counts for a church"""
        new_friends_count = CustomUser.objects.filter(
            church=church, 
            is_new_friend=True, 
            is_active=True
        ).count()
        
        regulars_count = CustomUser.objects.filter(
            church=church, 
            is_new_friend=False, 
            is_active=True
        ).count()
        
        total_members = new_friends_count + regulars_count
        
        return {
            'new_friends_count': new_friends_count,
            'regulars_count': regulars_count,
            'total_members': total_members,
        }
    
    def get_role_breakdown(self, church):
        """Get regular members breakdown by role"""
        vsl_count = CustomUser.objects.filter(
            church=church, role__name='VSL', is_new_friend=False, is_active=True
        ).count()
        csl_count = CustomUser.objects.filter(
            church=church, role__name='CSL', is_new_friend=False, is_active=True
        ).count()
        cl_count = CustomUser.objects.filter(
            church=church, role__name='CL', is_new_friend=False, is_active=True
        ).count()
        cm_count = CustomUser.objects.filter(
            church=church, role__name='CM', is_new_friend=False, is_active=True
        ).count()
        
        # Calculate percentages
        total_regulars = vsl_count + csl_count + cl_count + cm_count
        vsl_percentage = round((vsl_count / total_regulars * 100) if total_regulars > 0 else 0, 1)
        csl_percentage = round((csl_count / total_regulars * 100) if total_regulars > 0 else 0, 1)
        cl_percentage = round((cl_count / total_regulars * 100) if total_regulars > 0 else 0, 1)
        cm_percentage = round((cm_count / total_regulars * 100) if total_regulars > 0 else 0, 1)
        
        return {
            'vsl_count': vsl_count,
            'csl_count': csl_count,
            'cl_count': cl_count,
            'cm_count': cm_count,
            'vsl_percentage': vsl_percentage,
            'csl_percentage': csl_percentage,
            'cl_percentage': cl_percentage,
            'cm_percentage': cm_percentage,
        }


class ChartDataMixin:
    """Mixin for chart data generation"""
    
    def get_monthly_growth_data(self, church, months=6):
        """Get monthly growth data for charts"""
        months_list = []
        new_friends_monthly = []
        regulars_monthly = []
        
        for i in range(months):
            date = timezone.now() - timedelta(days=30*i)
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(seconds=1)
            
            months_list.append(month_start.strftime('%b %Y'))
            
            # Count new friends for this month
            month_new_friends = CustomUser.objects.filter(
                church=church,
                is_new_friend=True,
                date_joined__gte=month_start,
                date_joined__lte=month_end,
                is_active=True
            ).count()
            new_friends_monthly.append(month_new_friends)
            
            # Count regular members for this month
            month_regulars = CustomUser.objects.filter(
                church=church,
                is_new_friend=False,
                date_joined__gte=month_start,
                date_joined__lte=month_end,
                is_active=True
            ).count()
            regulars_monthly.append(month_regulars)
        
        # Reverse to show oldest to newest
        months_list.reverse()
        new_friends_monthly.reverse()
        regulars_monthly.reverse()
        
        return {
            'months': months_list,
            'new_friends_monthly': new_friends_monthly,
            'regulars_monthly': regulars_monthly,
        }
    
    def get_activity_trends(self, church, days=7):
        """Get activity trends for the last N days"""
        activity_trends = []
        
        for i in range(days):
            date = timezone.now() - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1) - timedelta(seconds=1)
            
            daily_activities = ActivityLog.objects.filter(
                user__church=church,
                timestamp__gte=day_start,
                timestamp__lte=day_end
            ).count()
            
            activity_trends.append({
                'date': date.strftime('%a'),
                'count': daily_activities
            })
        
        activity_trends.reverse()
        return activity_trends
    
    def get_role_distribution(self, church, regulars_count):
        """Get role distribution data for charts"""
        role_distribution = []
        roles = Role.objects.filter(name__in=['VSL', 'CSL', 'CL', 'CM'])
        
        for role in roles:
            count = CustomUser.objects.filter(
                church=church,
                role=role,
                is_new_friend=False,
                is_active=True
            ).count()
            
            if count > 0:
                role_distribution.append({
                    'role': role.get_name_display(),
                    'count': count,
                    'percentage': round((count / regulars_count * 100) if regulars_count > 0 else 0, 1)
                })
        
        return role_distribution


class ActivityLogMixin:
    """Mixin for activity log functionality"""
    
    def get_recent_activity(self, church, activity_date_filter=None, limit=5):
        """Get recent activity with optional date filter"""
        recent_activity_query = ActivityLog.objects.filter(user__church=church)
        
        if activity_date_filter:
            try:
                from datetime import datetime
                # Parse the date filter
                filter_date = datetime.strptime(activity_date_filter, '%Y-%m-%d').date()
                # Filter activities for the specific date
                recent_activity_query = recent_activity_query.filter(
                    timestamp__date=filter_date
                )
            except ValueError:
                # If date parsing fails, use default (last 7 days)
                pass
        
        # If no date filter or invalid date, show last 7 days by default
        if not activity_date_filter:
            week_ago = timezone.now() - timedelta(days=7)
            recent_activity_query = recent_activity_query.filter(timestamp__gte=week_ago)
        
        # Limit and order by timestamp
        recent_activity = recent_activity_query.select_related('user').order_by('-timestamp')[:limit]
        
        return recent_activity


class TransitionDataMixin:
    """Mixin for new friend to regular member transition data"""
    
    def get_transition_data(self, church, months=6):
        """Get monthly transition statistics"""
        transition_months = []
        transition_counts = []
        
        for i in range(months):
            date = timezone.now() - timedelta(days=30*i)
            month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = month_start + timedelta(days=32)
            month_end = month_end.replace(day=1) - timedelta(seconds=1)
            
            transition_months.append(month_start.strftime('%b %Y'))
            
            # Count transitions in this month
            month_transitions = CustomUser.objects.filter(
                church=church,
                is_new_friend=False,
                transition_date__gte=month_start,
                transition_date__lte=month_end,
                is_active=True
            ).count()
            transition_counts.append(month_transitions)
        
        # Reverse to show oldest to newest
        transition_months.reverse()
        transition_counts.reverse()
        
        return {
            'transition_months': transition_months,
            'transition_counts': transition_counts,
        }
    
    def get_current_month_transition_rate(self, church, new_friends_count):
        """Get transition rate for current month"""
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_transitions = CustomUser.objects.filter(
            church=church,
            is_new_friend=False,
            transition_date__gte=current_month_start,
            is_active=True
        ).count()
        
        # Calculate transition rate percentage
        transition_rate = round((current_month_transitions / new_friends_count * 100) if new_friends_count > 0 else 0, 1)
        
        return {
            'current_month_transitions': current_month_transitions,
            'transition_rate': transition_rate,
        }
