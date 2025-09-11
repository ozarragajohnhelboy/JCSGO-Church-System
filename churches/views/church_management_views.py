from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction, models
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from members.models import Church
from churches.models import ChurchSettings
from churches.forms import ChurchForm


@login_required
def church_list(request):
    """Display list of all churches with pagination"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('churches:dashboard')
    
    # Get search and filter parameters
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'name')
    
    # Get all churches
    churches = Church.objects.all()
    
    # Apply search filter
    if search:
        churches = churches.filter(
            models.Q(name__icontains=search) |
            models.Q(location__icontains=search) |
            models.Q(domain__icontains=search)
        )
    
    # Apply status filter
    if status_filter == 'active':
        churches = churches.filter(is_active=True)
    elif status_filter == 'inactive':
        churches = churches.filter(is_active=False)
    
    # Apply sorting
    if sort_by == 'location':
        churches = churches.order_by('location')
    elif sort_by == 'created_at':
        churches = churches.order_by('-created_at')
    elif sort_by == 'total_members':
        # This would require a custom ordering, for now just order by name
        churches = churches.order_by('name')
    else:
        churches = churches.order_by('name')
    
    # Pagination
    paginator = Paginator(churches, 10)  # 10 churches per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate active churches count
    active_churches_count = Church.objects.filter(is_active=True).count()
    
    context = {
        'page_obj': page_obj,
        'churches': page_obj,
        'total_churches': Church.objects.count(),
        'active_churches_count': active_churches_count,
        'search': search,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    return render(request, 'churches/church_management/church_list.html', context)


@login_required
def add_church(request):
    """Add a new church"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('churches:dashboard')
    
    if request.method == 'POST':
        form = ChurchForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create the church
                    church = form.save()
                    
                    # Create default church settings
                    ChurchSettings.objects.create(
                        church=church,
                        allow_public_registration=True,
                        require_email_verification=True,
                        require_admin_approval=False,
                        show_new_friends_count=True,
                        show_regulars_count=True,
                        show_growth_charts=True,
                        show_member_contact_info=False,
                        allow_member_directory=False,
                    )
                    
                    messages.success(request, f'Church "{church.name}" has been successfully created!')
                    return redirect('churches:church_list')
            except Exception as e:
                messages.error(request, f'Error creating church: {str(e)}')
    else:
        form = ChurchForm()
    
    context = {
        'form': form,
        'title': 'Add New Church',
    }
    return render(request, 'churches/church_management/church_form.html', context)


@login_required
def edit_church(request, church_id):
    """Edit an existing church"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('churches:dashboard')
    
    church = get_object_or_404(Church, id=church_id)
    
    if request.method == 'POST':
        form = ChurchForm(request.POST, request.FILES, instance=church)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Church "{church.name}" has been successfully updated!')
                return redirect('churches:church_list')
            except Exception as e:
                messages.error(request, f'Error updating church: {str(e)}')
    else:
        form = ChurchForm(instance=church)
    
    context = {
        'form': form,
        'church': church,
        'title': f'Edit Church: {church.name}',
    }
    return render(request, 'churches/church_management/church_form.html', context)


@login_required
def delete_church(request, church_id):
    """Delete a church"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('churches:dashboard')
    
    church = get_object_or_404(Church, id=church_id)
    
    if request.method == 'POST':
        try:
            church_name = church.name
            church.delete()
            messages.success(request, f'Church "{church_name}" has been successfully deleted!')
        except Exception as e:
            messages.error(request, f'Error deleting church: {str(e)}')
        
        return redirect('churches:church_list')
    
    context = {
        'church': church,
    }
    return render(request, 'churches/church_management/church_confirm_delete.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_church_status(request, church_id):
    """Toggle church active status via AJAX"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'Permission denied'})
    
    try:
        church = get_object_or_404(Church, id=church_id)
        church.is_active = not church.is_active
        church.save()
        
        return JsonResponse({
            'success': True,
            'is_active': church.is_active,
            'message': f'Church "{church.name}" is now {"active" if church.is_active else "inactive"}'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def church_detail(request, church_id):
    """View church details"""
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('churches:dashboard')
    
    church = get_object_or_404(Church, id=church_id)
    
    # Get church statistics
    from members.models import CustomUser
    total_members = church.members.filter(is_active=True).count()
    new_friends = church.members.filter(is_active=True, is_new_friend=True).count()
    regular_members = church.members.filter(is_active=True, is_new_friend=False).count()
    
    # Get recent members
    recent_members = church.members.filter(is_active=True).order_by('-date_joined')[:10]
    
    context = {
        'church': church,
        'total_members': total_members,
        'new_friends': new_friends,
        'regular_members': regular_members,
        'recent_members': recent_members,
    }
    return render(request, 'churches/church_management/church_detail.html', context)
