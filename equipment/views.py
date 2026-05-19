from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
import csv
from django.utils import timezone
from django import forms
from django.core.paginator import Paginator
from .models import Equipment, Requisition, Category
from .forms import RequisitionForm, EquipmentForm, RequisitionFilterForm

# Create your views here.
@login_required
def dashboard(request):
    equipment_count = Equipment.objects.count()
    requisition_count = Requisition.objects.count()
    pending_count = Requisition.objects.filter(status='PENDING').count()
    my_pending_count = Requisition.objects.filter(user=request.user, status='PENDING').count()
    
    context = {
        'equipment_count': equipment_count,
        'requisition_count': requisition_count,
        'pending_count': pending_count,
        'my_pending_count': my_pending_count,
    }
    return render(request, 'dashboard.html', context)

@login_required
def equipment_list(request):
    equipment_list = Equipment.objects.all().order_by('-pk')
    return render(request, 'equipment_list.html', {'equipment_list': equipment_list})

@login_required
def search_equipment(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    
    if query:
        equipment_list = Equipment.objects.filter(
            Q(name__icontains=query) | 
            Q(serial_number__icontains=query) |
            Q(category__name__icontains=query)
        ).order_by('-pk')
    else:
        equipment_list = Equipment.objects.all().order_by('-pk')
        
    paginator = Paginator(equipment_list, 8) # 8 items per page
    page_obj = paginator.get_page(page_number)
    
    results = list(page_obj.object_list.values('id', 'name', 'serial_number', 'available_quantity', 'image', 'status', 'category__name'))
    
    data = {
        'results': results,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'num_pages': paginator.num_pages,
        'current_page': page_obj.number,
    }
        
    return JsonResponse(data)

# @login_required
# def add_to_cart(request, equipment_id):
#     cart = request.session.get('cart', [])
#     if equipment_id not in cart:
#         cart.append(equipment_id)
#         request.session['cart'] = cart
#     return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

# @login_required
# def remove_from_cart(request, equipment_id):
#     cart = request.session.get('cart', [])
#     if equipment_id in cart:
#         cart.remove(equipment_id)
#         request.session['cart'] = cart
#     return redirect('cart_detail')

# @login_required
# def clear_cart(request):
#     request.session['cart'] = []
#     return redirect('cart_detail')

# @login_required
# def cart_detail(request):
#     cart = request.session.get('cart', [])
#     equipment_in_cart = Equipment.objects.filter(id__in=cart)
#     return render(request, 'cart_detail.html', {'equipment_list': equipment_in_cart})

# @login_required
# def checkout(request):
#     cart = request.session.get('cart', [])
#     if not cart:
#         return redirect('dashboard')

#     if request.method == 'POST':
#         return_date = request.POST.get('return_date') # Global return date for simplicity
        
#         for equipment_id in cart:
#             equipment = get_object_or_404(Equipment, pk=equipment_id)
            
#             # Get quantity from form
#             try:
#                 request_qty = int(request.POST.get(f'quantity_{equipment_id}', 1))
#             except (ValueError, TypeError):
#                 request_qty = 1
            
#             # Validate max quantity
#             if request_qty > equipment.available_quantity:
#                  request_qty = equipment.available_quantity # Cap at available? Or skip? Let's cap.

#             if request_qty > 0:
#                 # Create Requisition
#                 Requisition.objects.create(
#                     user=request.user,
#                     equipment=equipment,
#                     quantity=request_qty,
#                     return_date=return_date if return_date else None,
#                     status='PENDING'
#                 )
                
#                 # Deduct stock immediately
#                 equipment.available_quantity -= request_qty
#                 equipment.save()
#             else:
#                  # Skip invalid qty
#                  pass
                
#         # Clear cart
#         request.session['cart'] = []
#         return redirect('my_requests')
        
#     return redirect('cart_detail')

def equipment_request(request, equipment_id):
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    if request.method == 'POST':
        form = RequisitionForm(request.POST)
        if form.is_valid():
            requisition = form.save(commit=False)

            # Check availability (computed from total - active requisitions)
            request_qty = requisition.quantity
            if request_qty > equipment.available_quantity:
                form.add_error('quantity', f'Only {equipment.available_quantity} items available.')
                return render(request, 'request_form.html', {'form': form, 'equipment': equipment})

            if request.user.is_authenticated:
                requisition.user = request.user
            requisition.equipment = equipment
            requisition.save()

            if request.user.is_authenticated:
                return redirect('my_requests')
            return render(request, 'request_form.html', {'equipment': equipment, 'submitted': True})
    else:
        form = RequisitionForm()

    return render(request, 'request_form.html', {'form': form, 'equipment': equipment})

@login_required
def my_requests(request):
    requisitions = Requisition.objects.filter(user=request.user).order_by('-date')
    return render(request, 'my_requests.html', {'requisitions': requisitions, 'now': timezone.now()})

@login_required
def manage_requests(request):
    if not (request.user.is_staff == 1 or request.user.is_superuser == 1 or request.user.username == 'admin'):
        return redirect('dashboard')
    requisitions = Requisition.objects.all().order_by('-id')
    return render(request, 'manage_requests.html', {'requisitions': requisitions})

@login_required
def approve_request(request, requisition_id):
    if not (request.user.is_staff == 1 or request.user.is_superuser == 1 or request.user.username == 'admin'):
        return redirect('dashboard')

    requisition = get_object_or_404(Requisition, pk=requisition_id)

    if request.method == 'POST':
        requisition.status = 'APPROVED'
        requisition.approve_date = timezone.now()
        requisition.approved_by = request.user
        requisition.comment = request.POST.get('comment', '')
        requisition.save()

    return redirect('manage_requests')

@login_required
def reject_request(request, requisition_id):
    if not (request.user.is_staff == 1 or request.user.is_superuser == 1 or request.user.username == 'admin'):
        return redirect('dashboard')
        
    requisition = get_object_or_404(Requisition, pk=requisition_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reject_reason', '')

        requisition.status = 'REJECTED'
        requisition.reject_date = timezone.now()
        requisition.reject_reason = reason
        requisition.rejected_by = request.user
        requisition.save()

    return redirect('manage_requests')

@login_required
def receive_request(request, requisition_id):
    if not (request.user.is_staff == 1 or request.user.is_superuser == 1 or request.user.username == 'admin'):
        return redirect('dashboard')
        
    requisition = get_object_or_404(Requisition, pk=requisition_id)

    # Only process if currently Approved and submitted via POST
    if request.method == 'POST' and requisition.status == 'APPROVED':
        requisition.status = 'RETURNED'
        requisition.actual_return_date = timezone.now()
        requisition.received_by = request.user
        requisition.receive_comment = request.POST.get('comment', '')
        requisition.save()

    return redirect('manage_requests')

@login_required
def scan_qr(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    return render(request, 'scan_qr.html')

@login_required
def request_report(request):
    if not (request.user.is_staff == 1 or request.user.is_superuser == 1 or request.user.username == 'admin'):
        return redirect('dashboard')
        
    form = RequisitionFilterForm(request.GET)
    requisitions = None
    
    # Check if any filter parameters are present (even if empty strings)
    # This implies the user clicked "Filter"
    if request.GET:
        if form.is_valid():
            requisitions = Requisition.objects.all().order_by('-date')
            
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            category = form.cleaned_data.get('category')
            
            if start_date:
                requisitions = requisitions.filter(date__date__gte=start_date)
            if end_date:
                requisitions = requisitions.filter(date__date__lte=end_date)
            if category:
                requisitions = requisitions.filter(equipment__category=category)
                
            # CSV Export
            if request.GET.get('export') == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="requisition_report.csv"'
                
                writer = csv.writer(response)
                writer.writerow(['ID', 'Equipment', 'Quantity', 'User', 'Request Date', 'Approve Date', 'Reject Date', 'Returned Date', 'Status'])
                
                for req in requisitions:
                    writer.writerow([
                        req.pk,
                        req.equipment.name,
                        req.quantity,
                        req.user.username if req.user else (req.borrower_name or '-'),
                        req.date.strftime('%Y-%m-%d %H:%M'),
                        req.approve_date.strftime('%Y-%m-%d %H:%M') if req.approve_date else '-',
                        req.reject_date.strftime('%Y-%m-%d %H:%M') if req.reject_date else '-',
                        req.actual_return_date.strftime('%Y-%m-%d %H:%M') if req.actual_return_date else '-',
                        req.get_status_display()
                    ])
                
                return response
            
    return render(request, 'request_report.html', {'requisitions': requisitions, 'form': form})

@login_required
def add_equipment(request):
    if not request.user.is_staff:
        return redirect('equipment_list')
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('equipment_list')
    else:
        form = EquipmentForm()
    
    return render(request, 'add_equipment.html', {'form': form})

@login_required
def edit_equipment(request, equipment_id):
    if not request.user.is_staff:
        return redirect('equipment_list')
    
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        if form.is_valid():
            form.save()
            return redirect('equipment_list')
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'edit_equipment.html', {'form': form, 'equipment': equipment})

@login_required
def delete_equipment(request, equipment_id):
    if not request.user.is_staff:
        return redirect('equipment_list')
    
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    if request.method == 'POST':
        equipment.delete()
        return redirect('equipment_list')
    
    return redirect('equipment_list')

