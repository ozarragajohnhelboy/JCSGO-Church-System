from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import get_user_model

from ..models import CustomUser, NewFriend, RegularMember, Role

User = get_user_model()


@login_required
def member_list(request):
    """List all members for the user's church"""
    user = request.user
    church = user.church
    
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    
    members = CustomUser.objects.filter(church=church, is_active=True)
    
    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    if role_filter:
        members = members.filter(role__name=role_filter)
    
    if status_filter == 'new_friends':
        members = members.filter(is_new_friend=True)
    elif status_filter == 'regular_members':
        members = members.filter(is_new_friend=False)
    
    members = members.order_by('first_name', 'last_name')
    
    paginator = Paginator(members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    roles = Role.objects.filter(
        name__in=['VSL', 'CSL', 'CL', 'CM']
    ).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': roles,
        'total_members': members.count(),
        'new_friends_count': members.filter(is_new_friend=True).count(),
        'regular_members_count': members.filter(is_new_friend=False).count(),
    }
    
    return render(request, 'members/members/member_list.html', context)


@login_required
def member_detail(request, pk):
    """Detailed view of a member"""
    user = request.user
    member = get_object_or_404(CustomUser, pk=pk)
    
    if not user.can_access_church_data(member.church):
        messages.error(request, 'You do not have permission to view this member.')
        return redirect('members:member_list')
    
    from_page = request.GET.get('from', '')
    
    if from_page == 'new_friends':
        back_url = 'members:new_friends_list'
    elif from_page == 'regular_members':
        back_url = 'members:regular_members_list'
    elif from_page == 'role_new_friends':
        back_url = 'members:role_new_friends_list'
    else:
        # Default behavior - determine by member type and user role
        back_url = 'members:member_list'
        
        if user.role.name in ['VSL', 'CSL', 'CL'] and member.is_new_friend:
            try:
                new_friend_profile = member.new_friend_profile
                if new_friend_profile.endorsed_to == user:
                    back_url = 'members:role_new_friends_list'
            except NewFriend.DoesNotExist:
                pass
    
    new_friend_profile = None
    regular_member_profile = None
    
    if member.is_new_friend:
        try:
            new_friend_profile = member.new_friend_profile
        except NewFriend.DoesNotExist:
            pass
    else:
        try:
            regular_member_profile = member.regular_member_profile
        except RegularMember.DoesNotExist:
            pass
    
    recent_activity = member.activity_logs.order_by('-timestamp')[:10]
    
    group_membership = None
    if regular_member_profile and regular_member_profile.group:
        group_membership = regular_member_profile.group
    
    context = {
        'member': member,
        'new_friend_profile': new_friend_profile,
        'regular_member_profile': regular_member_profile,
        'recent_activity': recent_activity,
        'group_membership': group_membership,
        'activity_summary': member.get_activity_summary(),
        'back_url': back_url,
    }
    
    return render(request, 'members/members/member_detail.html', context)


@login_required
def new_friends_list(request):
    """List all new friends for the user's church"""
    user = request.user
    church = user.church
    
    search = request.GET.get('search', '')
    follow_up_status = request.GET.get('follow_up_status', '')
    timer_status = request.GET.get('timer_status', '')
    
    new_friends_users = CustomUser.objects.filter(
        church=church,
        is_active=True,
        is_new_friend=True
    )
    
    if search:
        new_friends_users = new_friends_users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(new_friend_profile__invited_by__first_name__icontains=search) |
            Q(new_friend_profile__invited_by__last_name__icontains=search)
        )
    
    if timer_status:
        new_friends_users = new_friends_users.filter(timer_status=timer_status)

    new_friends = []
    for user_obj in new_friends_users:
        try:
            new_friend_profile = NewFriend.objects.get(user=user_obj)
            if follow_up_status and new_friend_profile.follow_up_status != follow_up_status:
                continue
            new_friends.append(new_friend_profile)
        except NewFriend.DoesNotExist:
            continue
    
    paginator = Paginator(new_friends, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'follow_up_status': follow_up_status,
        'timer_status': timer_status,
        'total_new_friends': len(new_friends),
    }
    
    return render(request, 'members/members/new_friends_list.html', context)


@login_required
def regular_members_list(request):
    """List all regular members for the user's church"""
    user = request.user
    church = user.church
    
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    group_filter = request.GET.get('group', '')
    
    regular_members_users = CustomUser.objects.filter(
        church=church,
        is_active=True,
        is_new_friend=False
    )
    
    if search:
        regular_members_users = regular_members_users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    if role_filter:
        regular_members_users = regular_members_users.filter(role__name=role_filter)
    
    if group_filter:
        regular_members_users = regular_members_users.filter(
            regular_member_profile__group__name__icontains=group_filter
        )
    
    regular_members = []
    for user_obj in regular_members_users:
        try:
            regular_member_profile = RegularMember.objects.get(user=user_obj)
            regular_members.append(regular_member_profile)
        except RegularMember.DoesNotExist:
            continue
    
    paginator = Paginator(regular_members, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    roles = Role.objects.filter(
        name__in=['VSL', 'CSL', 'CL', 'CM']
    ).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'role_filter': role_filter,
        'group_filter': group_filter,
        'roles': roles,
        'total_regular_members': len(regular_members),
    }
    
    return render(request, 'members/members/regular_members_list.html', context)
