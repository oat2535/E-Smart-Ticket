from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .utils import get_user_role
from django.contrib.auth import login
from django.contrib.admin.views.decorators import staff_member_required
from .models import AccessRequest, System, AccessRequestLog
from .forms import AccessRequestForm
from django.core.mail import send_mail
from django.conf import settings
import threading

def log_action(request, access_request, action, details=''):
    AccessRequestLog.objects.create(
        access_request=access_request,
        actor=request.user,
        action=action,
        details=details
    )

def _send_notification_email_sync(access_request, subject, message):
    try:
        # Check if email is configured (simulated for now if not in settings)
        # In production, ensure EMAIL_HOST etc. are set in settings.py
        recipient_list = [access_request.email]
        if access_request.user and access_request.user.email:
            recipient_list.append(access_request.user.email)
            
        send_mail(
            subject=f"[Access Request] {subject}",
            message=message,
            from_email=None, # Use default
            recipient_list=list(set(recipient_list)), # Unique
            fail_silently=True
        )
    except Exception as e:
        print(f"Failed to send email: {e}")

def send_notification_email(access_request, subject, message):
    threading.Thread(target=_send_notification_email_sync, args=(access_request, subject, message)).start()

@login_required
def dashboard(request):
    user_role = get_user_role(request.user)
    if user_role in ['manager', 'it', 'admin']:
        all_requests_qs = AccessRequest.objects.all()
    else:
        all_requests_qs = AccessRequest.objects.filter(user=request.user)
    
    pending_manager_count = all_requests_qs.filter(status='pending_manager').count()
    pending_it_count = all_requests_qs.filter(status='pending_it').count()
    approved_count = all_requests_qs.filter(status='approved').count()
    rejected_count = all_requests_qs.filter(status='rejected').count()
    
    status_filter = request.GET.get('status')
    if status_filter == 'pending_manager':
        requests_qs = all_requests_qs.filter(status='pending_manager').order_by('-created_at')
    elif status_filter == 'pending_it':
        requests_qs = all_requests_qs.filter(status='pending_it').order_by('-created_at')
    elif status_filter == 'approved':
        requests_qs = all_requests_qs.filter(status='approved').order_by('-created_at')
    elif status_filter == 'rejected':
        requests_qs = all_requests_qs.filter(status='rejected').order_by('-created_at')
    else:
        requests_qs = all_requests_qs.order_by('-created_at')
    
    grouped_requests = []
    groups = {}
    for req in requests_qs:
        time_key = req.created_at.strftime('%Y-%m-%d %H:%M')
        key = f"{req.employee_id}_{time_key}"
        
        if key not in groups:
            groups[key] = {
                'pk': req.pk,
                'request_code': req.request_code,
                'firstname_th': req.firstname_th,
                'lastname_th': req.lastname_th,
                'created_at': req.created_at,
                'systems': []
            }
            grouped_requests.append(groups[key])
            
        for sys in req.systems.all():
            if req.status == 'pending_manager':
                tooltip = "รอหัวหน้าอนุมัติ (Wait for Manager)"
            elif req.status == 'pending_it':
                tooltip = "รอฝ่าย IT อนุมัติ (Wait for IT)"
            elif req.status == 'approved':
                approver = req.it_approver.get_full_name() if req.it_approver else 'IT'
                tooltip = f"อนุมัติแล้วโดย {approver}"
            elif req.status == 'rejected':
                rejecter = req.rejected_by.get_full_name() if req.rejected_by else 'ผู้พิจารณา'
                tooltip = f"ถูกปฏิเสธโดย {rejecter}"
            else:
                tooltip = req.get_status_display()
                
            groups[key]['systems'].append({
                'name': sys.name,
                'status': req.status,
                'tooltip': tooltip,
            })
            
    context = {
        'grouped_requests': grouped_requests, 
        'pending_manager_count': pending_manager_count,
        'pending_it_count': pending_it_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'access_requests/dashboard.html', context)

@login_required
def request_list(request):
    requests_qs = AccessRequest.objects.filter(user=request.user).order_by('-created_at')
    
    grouped_requests = []
    groups = {}
    for req in requests_qs:
        time_key = req.created_at.strftime('%Y-%m-%d %H:%M')
        key = f"{req.employee_id}_{time_key}"
        
        if key not in groups:
            groups[key] = {
                'pk': req.pk,
                'request_code': req.request_code,
                'firstname_th': req.firstname_th,
                'lastname_th': req.lastname_th,
                'created_at': req.created_at,
                'systems': []
            }
            grouped_requests.append(groups[key])
            
        for sys in req.systems.all():
            if req.status == 'pending_manager':
                tooltip = "รอหัวหน้าอนุมัติ (Wait for Manager)"
            elif req.status == 'pending_it':
                tooltip = "รอฝ่าย IT อนุมัติ (Wait for IT)"
            elif req.status == 'approved':
                approver = req.it_approver.get_full_name() if req.it_approver else 'IT'
                tooltip = f"อนุมัติแล้วโดย {approver}"
            elif req.status == 'rejected':
                rejecter = req.rejected_by.get_full_name() if req.rejected_by else 'ผู้พิจารณา'
                tooltip = f"ถูกปฏิเสธโดย {rejecter}"
            else:
                tooltip = req.get_status_display()
                
            groups[key]['systems'].append({
                'name': sys.name,
                'status': req.status,
                'tooltip': tooltip,
            })
            
    return render(request, 'access_requests/request_list.html', {'grouped_requests': grouped_requests})

@login_required
def create_request(request):
    if request.method == 'POST':
        form = AccessRequestForm(request.POST)
        if form.is_valid():
            selected_systems = form.cleaned_data.pop('systems')
            data = form.cleaned_data
            
            for system in selected_systems:
                access_request = AccessRequest(**data)
                access_request.user = request.user
                access_request.save()
                access_request.systems.add(system)
                
                # Log and Notify
                log_action(request, access_request, 'Created', 'Created new request')
                send_notification_email(access_request, "Received Request", f"Your request {access_request.request_code} for {system.name} has been received and is pending manager approval.")
                
            return redirect('access_dashboard')
    else:
        # Pre-fill email if available
        initial_data = {}
        if request.user.email:
            initial_data['email'] = request.user.email
        form = AccessRequestForm(initial=initial_data)
    return render(request, 'access_requests/request_form.html', {'form': form})

@login_required
def request_detail(request, pk):
    access_request = get_object_or_404(AccessRequest, pk=pk)
    user_role = get_user_role(request.user)
    if access_request.user != request.user and user_role not in ['manager', 'it', 'admin']:
        return redirect('access_dashboard')
        
    start_time = access_request.created_at.replace(second=0, microsecond=0)
    end_time = start_time + timezone.timedelta(minutes=1)
    
    grouped_reqs = AccessRequest.objects.filter(
        employee_id=access_request.employee_id,
        created_at__gte=start_time,
        created_at__lt=end_time
    )
        
    return render(request, 'access_requests/request_detail.html', {
        'request_obj': access_request,
        'grouped_reqs': grouped_reqs
    })

# Manager / Admin Views

@login_required
def approval_list(request):
    from django.core.paginator import Paginator

    user_role = get_user_role(request.user)
    if user_role not in ['manager', 'it', 'admin']:
        return redirect('access_dashboard')

    systems = System.objects.all()
    
    if user_role == 'manager':
        pending_requests = AccessRequest.objects.filter(status='pending_manager').order_by('-created_at')
        total_pending = AccessRequest.systems.through.objects.filter(accessrequest__status='pending_manager').count()
    else: # IT or admin
        pending_requests = AccessRequest.objects.filter(status__in=['pending_manager', 'pending_it']).order_by('-created_at')
        total_pending = AccessRequest.systems.through.objects.filter(accessrequest__status__in=['pending_manager', 'pending_it']).count()
    
    selected_system_id = request.GET.get('system_id')
    
    if not selected_system_id and systems.exists():
        selected_system_id = str(systems.first().id)
        
    system_data = []
    for sys in systems:
        sys_count = pending_requests.filter(systems=sys).count()
        system_data.append({
            'system': sys,
            'count': sys_count,
            'is_active': str(sys.id) == str(selected_system_id)
        })
        
    if selected_system_id:
        active_requests = pending_requests.filter(systems__id=selected_system_id)
    else:
        active_requests = pending_requests
        
    paginator = Paginator(active_requests, 10)
    page_number = request.GET.get('page')
    requests_page = paginator.get_page(page_number)
    
    context = {
        'system_data': system_data,
        'requests': requests_page,
        'total_pending': total_pending,
        'selected_system_id': selected_system_id,
        'user_role': user_role
    }
    
    return render(request, 'access_requests/approval_list.html', context)

@login_required
def approve_request(request, pk):
    if request.method == 'POST':
        user_role = get_user_role(request.user)
        access_request = get_object_or_404(AccessRequest, pk=pk)
        
        if access_request.status == 'pending_manager' and user_role in ['manager', 'admin']:
            # Manager Approval -> Send to IT
            access_request.status = 'pending_it'
            access_request.manager_approver = request.user
            access_request.manager_approval_date = timezone.now()
            access_request.manager_comment = request.POST.get('comment', '')
            access_request.save()
            
            log_action(request, access_request, 'Manager Approved', f"Comment: {access_request.manager_comment}")
            send_notification_email(access_request, "Manager Approved", f"Your request {access_request.request_code} has been approved by Manager. Waiting for IT approval.")
            
        elif access_request.status == 'pending_it' and user_role in ['it', 'admin']:
            # IT Approval -> Final Approved
            access_request.status = 'approved'
            access_request.it_approver = request.user
            access_request.it_approval_date = timezone.now()
            # access_request.it_comment = request.POST.get('comment', '') # If needed
            access_request.save()
            
            log_action(request, access_request, 'IT Approved', "Final Approval")
            send_notification_email(access_request, "Access Granted", f"Congratulations! Your request {access_request.request_code} has been fully approved.")
            
    return redirect('access_approval_list')

@login_required
def reject_request(request, pk):
    if request.method == 'POST':
        user_role = get_user_role(request.user)
        access_request = get_object_or_404(AccessRequest, pk=pk)
        
        if (access_request.status == 'pending_manager' and user_role not in ['manager', 'admin']) or \
           (access_request.status == 'pending_it' and user_role not in ['it', 'admin']):
            return redirect('access_approval_list')

        previous_status = access_request.status
        access_request.status = 'rejected'
        access_request.reject_reason = request.POST.get('reason', '')
        
        # Record who rejected
        access_request.rejected_by = request.user
        access_request.rejected_at = timezone.now()
        
        if previous_status == 'pending_manager':
            access_request.manager_approver = request.user 
        elif previous_status == 'pending_it':
            access_request.it_approver = request.user
            
        access_request.save()
        
        log_action(request, access_request, 'Rejected', f"Reason: {access_request.reject_reason}")
        send_notification_email(access_request, "Request Rejected", f"Your request {access_request.request_code} has been rejected. Reason: {access_request.reject_reason}")

    return redirect('access_approval_list')

def public_create_request(request):
    """
    Allow users to request access without logging in.
    """
    if request.method == 'POST':
        form = AccessRequestForm(request.POST)
        if form.is_valid():
            selected_systems = form.cleaned_data.pop('systems')
            data = form.cleaned_data
            
            for system in selected_systems:
                access_request = AccessRequest(**data)
                access_request.user = None # Public request has no user initially
                access_request.save()
                access_request.systems.add(system)
                
                # Log action (actor is None for public)
                AccessRequestLog.objects.create(
                    access_request=access_request,
                    actor=None,
                    action='Created (Public)',
                    details=f'Created new request via public form for {system.name}'
                )
                
                # Send email
                send_notification_email(access_request, "Received Request", f"Your request {access_request.request_code} for {system.name} has been received and is pending manager approval.")
            
            # For public request success page, we just pass the last request code, or tell them it was submitted
            return render(request, 'access_requests/request_success.html', {'request_code': access_request.request_code})
    else:
        form = AccessRequestForm()
    return render(request, 'access_requests/request_form.html', {'form': form, 'is_public': True})
