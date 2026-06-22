from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from sub_branch.models import SubBranch
from .models import MasterAsset, SubAsset, AssetTransfer, MaintenanceRecord, AssetWriteOff, AssetDisposal, DisposalImage, AssetInventory, AssetImage
from .forms import AssetTransferForm, MaintenanceRecordForm, AssetWriteOffForm, AssetDisposalForm, DisposalImageForm, AssetInventoryForm
import qrcode
import os
from io import BytesIO
import base64
import pymssql
import json

@login_required
def asset_list(request):
    assets = MasterAsset.objects.all().order_by('-id')
    return render(request, 'assets_system/asset_list.html', {'assets': assets})

@login_required
def asset_detail(request, asset_id):
    asset = get_object_or_404(MasterAsset, pk=asset_id)
    
    # Handled via AJAX now
    
    # Generate QR Code
    scan_url = request.build_absolute_uri(f'/assets/scan/{asset.id}/')
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(scan_url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_img = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'asset': asset,
        'qr_code': qr_code_img,
        'latest_audit': asset.inventories.order_by('scanned_at').last(),
    }
    return render(request, 'assets_system/asset_detail.html', context)

@login_required
def print_qr_codes(request):
    ids_param = request.GET.get('ids', '')
    if not ids_param:
        messages.error(request, 'ไม่ได้เลือกทรัพย์สิน')
        return redirect('assets_system:asset_list')
        
    ids = [int(id_str) for id_str in ids_param.split(',') if id_str.strip().isdigit()]
    assets = MasterAsset.objects.filter(id__in=ids)
    
    # Pre-calculate scan URLs for each asset to pass to template
    asset_data = []
    for asset in assets:
        scan_url = request.build_absolute_uri(f'/assets/scan/{asset.id}/')
        asset_data.append({
            'asset_code': asset.asset_code,
            'name': asset.name,
            'scan_url': scan_url
        })
        
    return render(request, 'assets_system/print_qr_codes.html', {'assets': asset_data})

@login_required
def request_transfer(request, asset_id):
    asset = get_object_or_404(MasterAsset, pk=asset_id)
    
    has_sub_branch = False
    company_name = ''
    company_id = None
    
    from sub_branch.models import SubBranch
    from branch.models import Branch
    
    user_branch_id = getattr(request.user.branch, 'branch_id', None)
    user_sub_branch_id = getattr(request.user.sub_branch, 'sub_branch_id', None)
    tp_override = False
    
    if asset.branch == 'TP' and user_branch_id == 'TLPH' and user_sub_branch_id == 'TP':
        has_sub_branch = False
        tp_override = True
        try:
            tp_sub = SubBranch.objects.get(sub_branch_id='TP')
            tp_branch = tp_sub.branch_id
            company_name = f"{tp_branch.branch_name} - {tp_sub.sub_branch_name}"
        except SubBranch.DoesNotExist:
            company_name = 'โรงพยาบาลสัตว์ทองหล่อฉลองภูเก็ต'
    else:
        try:
            SubBranch.objects.get(sub_branch_id=asset.branch)
            has_sub_branch = True
        except SubBranch.DoesNotExist:
            try:
                branch = Branch.objects.get(branch_id=asset.branch)
                company_name = branch.branch_name
                company_id = branch.branch_id
            except Branch.DoesNotExist:
                pass

    if request.method == 'POST':
        form = AssetTransferForm(request.POST, asset_branch_id=asset.branch)
        if form.is_valid():
            transfer = form.save(commit=False)
            transfer.asset = asset
            transfer.from_user = request.user
            
            if tp_override:
                transfer.from_company_id = 'TLPH'
                transfer.from_branch_id = 'TP'
                transfer.to_company_id = 'TLPH'
                transfer.to_branch_id = 'TP'
            elif has_sub_branch:
                # Force from_branch to user's sub_branch if they have one (security/enforcement)
                if hasattr(request.user, 'sub_branch') and request.user.sub_branch:
                    transfer.from_branch = request.user.sub_branch
                    
                # Automatically assign to_company based on the selected to_branch
                if transfer.to_branch and getattr(transfer.to_branch, 'branch_id', None):
                    transfer.to_company = transfer.to_branch.branch_id
                
                # Automatically assign from_company based on the selected from_branch
                if transfer.from_branch and getattr(transfer.from_branch, 'branch_id', None):
                    transfer.from_company = transfer.from_branch.branch_id
            else:
                if company_id:
                    transfer.to_company_id = company_id
                    transfer.from_company_id = company_id
                    
            transfer.save()
            return redirect('assets_system:transfer_list')
    else:
        initial_data = {}
        if hasattr(request.user, 'sub_branch') and request.user.sub_branch:
            initial_data['from_branch'] = request.user.sub_branch
        form = AssetTransferForm(asset_branch_id=asset.branch, initial=initial_data)
        
        # Make the from_branch select visually read-only if it's auto-stamped
        if hasattr(request.user, 'sub_branch') and request.user.sub_branch:
            form.fields['from_branch'].widget.attrs['style'] = 'pointer-events: none; background-color: #e9ecef;'
            form.fields['from_branch'].widget.attrs['tabindex'] = '-1'
        
    return render(request, 'assets_system/transfer_form.html', {
        'form': form, 
        'asset': asset,
        'has_sub_branch': has_sub_branch,
        'company_name': company_name
    })

@login_required
def request_writeoff(request, asset_id):
    # Check if user has permission (department must be IT, MED, or FM)
    user_dept = getattr(getattr(request.user, 'department', None), 'department_id', None)
    if user_dept not in ['IT', 'MED', 'FM'] and not request.user.is_superuser:
        messages.error(request, 'คุณไม่มีสิทธิ์ทำรายการแทงชำรุด (เฉพาะแผนก IT, MED, FM)')
        return redirect('assets_system:asset_detail', asset_id=asset_id)

    asset = get_object_or_404(MasterAsset, pk=asset_id)
    if request.method == 'POST':
        form = AssetWriteOffForm(request.POST)
        if form.is_valid():
            writeoff = form.save(commit=False)
            writeoff.asset = asset
            writeoff.assessed_by = request.user
            
            position_name = request.user.position.name if hasattr(request.user, 'position') and request.user.position else ''
            if position_name == 'ผู้จัดการ':
                writeoff.status = 'pending_accounting'
            else:
                writeoff.status = 'pending_head'
                
            writeoff.save()
            return redirect('assets_system:writeoff_list')
    else:
        form = AssetWriteOffForm()
    return render(request, 'assets_system/writeoff_form.html', {'form': form, 'asset': asset})

@login_required
def approve_writeoff(request, writeoff_id, action):
    writeoff = get_object_or_404(AssetWriteOff, pk=writeoff_id)
    position_name = request.user.position.name if hasattr(request.user, 'position') and request.user.position else ''
    is_superuser = request.user.is_superuser

    if writeoff.status == 'pending_head':
        if not (position_name == 'ผู้จัดการ' or is_superuser):
            messages.error(request, 'คุณไม่มีสิทธิ์อนุมัติรายการนี้')
            return redirect('assets_system:writeoff_list')
        
        if action == 'approve':
            writeoff.status = 'pending_accounting'
            writeoff.head_approver = request.user
        elif action == 'reject':
            writeoff.status = 'rejected'
            writeoff.head_approver = request.user
            if request.method == 'POST':
                writeoff.reject_reason = request.POST.get('reject_reason', '')
            
    elif writeoff.status == 'pending_accounting':
        if not (position_name == 'บัญชี' or is_superuser):
            messages.error(request, 'คุณไม่มีสิทธิ์อนุมัติรายการนี้')
            return redirect('assets_system:writeoff_list')
            
        if action == 'approve':
            writeoff.status = 'completed'
            writeoff.accounting_approver = request.user
            asset = writeoff.asset
            asset.status = 'written_off'
            asset.save()
        elif action == 'reject':
            writeoff.status = 'rejected'
            writeoff.accounting_approver = request.user
            if request.method == 'POST':
                writeoff.reject_reason = request.POST.get('reject_reason', '')
            
    writeoff.save()
    return redirect('assets_system:writeoff_list')

@login_required
def request_disposal(request, asset_id):
    asset = get_object_or_404(MasterAsset, pk=asset_id)
    if request.method == 'POST':
        form = AssetDisposalForm(request.POST)
        image_form = DisposalImageForm(request.POST, request.FILES)
        if form.is_valid() and image_form.is_valid():
            disposal = form.save(commit=False)
            disposal.asset = asset
            disposal.requested_by = request.user
            disposal.save()
            
            for img in image_form.cleaned_data.get('images', []):
                DisposalImage.objects.create(disposal=disposal, image=img)
                
            return redirect('assets_system:disposal_list')
    else:
        form = AssetDisposalForm()
        image_form = DisposalImageForm()
    return render(request, 'assets_system/disposal_form.html', {'form': form, 'image_form': image_form, 'asset': asset})

@login_required
def request_maintenance(request, asset_id):
    asset = get_object_or_404(MasterAsset, pk=asset_id)
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.asset = asset
            maintenance.reported_by = request.user
            maintenance.save()
            return redirect('assets_system:maintenance_list')
    else:
        form = MaintenanceRecordForm()
        form.fields['sub_asset'].queryset = SubAsset.objects.filter(master_asset=asset)
    return render(request, 'assets_system/maintenance_form.html', {'form': form, 'asset': asset})

@login_required
def scan_qr(request, asset_id):
    asset = get_object_or_404(MasterAsset, pk=asset_id)
    if request.method == 'POST':
        form = AssetInventoryForm(request.POST)
        if form.is_valid():
            inventory = form.save(commit=False)
            inventory.asset = asset
            inventory.scanned_by = request.user
            inventory.save()
            messages.success(request, 'บันทึกประวัติการตรวจนับเรียบร้อยแล้ว')
            if request.GET.get('iframe'):
                return redirect(f'/assets/{asset.id}/?iframe=1')
            return redirect('assets_system:asset_detail', asset_id=asset.id)
    
    # If GET request (e.g. scanned from mobile), redirect to detail page
    # The user can then click the "Audit" button on the detail page
    return redirect(f'/assets/{asset.id}/?iframe=1')

@login_required
def transfer_list(request):
    transfers = AssetTransfer.objects.all().order_by('-created_at')
    
    position_name = getattr(request.user.position, 'name', '') if hasattr(request.user, 'position') and request.user.position else ''
    department_id = getattr(request.user.department, 'department_id', '') if hasattr(request.user, 'department') and request.user.department else ''
    is_superuser = request.user.is_superuser
    
    if not (position_name == 'บัญชี' or department_id == 'IT' or is_superuser):
        user_branch = getattr(request.user, 'branch', None)
        from django.db.models import Q
        transfers = transfers.filter(Q(from_company=user_branch) | Q(to_company=user_branch))
        
    return render(request, 'assets_system/transfer_list.html', {'transfers': transfers})

@login_required
def maintenance_list(request):
    maintenances = MaintenanceRecord.objects.all().order_by('-created_at')
    return render(request, 'assets_system/maintenance_list.html', {'maintenances': maintenances})

@login_required
def writeoff_list(request):
    writeoffs = AssetWriteOff.objects.all().order_by('-created_at')
    return render(request, 'assets_system/writeoff_list.html', {'writeoffs': writeoffs})

@login_required
def disposal_list(request):
    disposals = AssetDisposal.objects.all().order_by('-created_at')
    return render(request, 'assets_system/disposal_list.html', {'disposals': disposals})

@login_required
def approve_maintenance(request, maintenance_id, action):
    # Only IT can approve
    is_it = request.user.is_superuser
    if not is_it:
        position_name = request.user.position.name if hasattr(request.user, 'position') and request.user.position else ''
        dept_name = request.user.department.department_name if hasattr(request.user, 'department') and request.user.department else ''
        if position_name.upper() == 'IT' or dept_name.upper() == 'IT':
            is_it = True

    if not is_it:
        messages.error(request, 'คุณไม่มีสิทธิ์อนุมัติรายการแจ้งซ่อม')
        return redirect('assets_system:maintenance_list')
        
    maintenance = get_object_or_404(MaintenanceRecord, pk=maintenance_id)
    if action == 'approve':
        maintenance.status = 'pending' # Moved to next status
    elif action == 'reject':
        maintenance.status = 'rejected'
        if request.method == 'POST':
            maintenance.reject_reason = request.POST.get('reject_reason', '')
    maintenance.save()
    return redirect('assets_system:maintenance_list')

@login_required
def load_sub_branches(request):
    company_id = request.GET.get('company_id')
    if company_id:
        sub_branches = SubBranch.objects.filter(branch_id_id=company_id).order_by('sub_branch_name')
    else:
        sub_branches = SubBranch.objects.none()
    return JsonResponse(list(sub_branches.values('sub_branch_id', 'sub_branch_name')), safe=False)

@login_required
def approve_transfer(request, transfer_id, action):
    transfer = get_object_or_404(AssetTransfer, pk=transfer_id)
    position_name = getattr(request.user.position, 'name', '') if hasattr(request.user, 'position') and request.user.position else ''
    position_id = getattr(request.user.position, 'id', None) if hasattr(request.user, 'position') and request.user.position else None
    is_superuser = request.user.is_superuser
    user_branch = getattr(request.user, 'branch', None)

    if transfer.status == 'pending_source_head':
        if not (position_name == 'ผู้จัดการ' and user_branch == transfer.from_company) and not is_superuser:
            messages.error(request, 'คุณไม่มีสิทธิ์อนุมัติรายการนี้')
            return redirect('assets_system:transfer_list')
        
        if action == 'approve':
            transfer.head_approver = request.user
            # Check if source company has sub_branches
            has_sub_branch = False
            if transfer.from_company:
                has_sub_branch = SubBranch.objects.filter(branch_id_id=transfer.from_company.branch_id).exists()
                
            if not has_sub_branch:
                transfer.status = 'pending_accounting'
            else:
                transfer.status = 'pending_destination_receive'
        elif action == 'reject':
            transfer.status = 'rejected'
            transfer.head_approver = request.user
            if request.method == 'POST':
                transfer.reject_reason = request.POST.get('reject_reason', '')
                
    elif transfer.status == 'pending_destination_receive':
        if not (position_id == 5 and user_branch == transfer.to_company) and not is_superuser:
            messages.error(request, 'คุณไม่มีสิทธิ์รับสินค้า')
            return redirect('assets_system:transfer_list')
            
        if action == 'receive':
            transfer.status = 'pending_destination_head'
            transfer.destination_received_by = request.user
            
    elif transfer.status == 'pending_destination_head':
        if not (position_name == 'ผู้จัดการ' and user_branch == transfer.to_company) and not is_superuser:
            messages.error(request, 'คุณไม่มีสิทธิ์อนุมัติรายการนี้')
            return redirect('assets_system:transfer_list')
            
        if action == 'approve':
            transfer.status = 'pending_accounting'
            transfer.destination_head_approver = request.user
        elif action == 'reject':
            transfer.status = 'rejected'
            transfer.destination_head_approver = request.user
            if request.method == 'POST':
                transfer.reject_reason = request.POST.get('reject_reason', '')
            
    elif transfer.status == 'pending_accounting':
        if not (position_name == 'บัญชี' or is_superuser):
            messages.error(request, 'คุณไม่มีสิทธิ์อนุมัติรายการนี้')
            return redirect('assets_system:transfer_list')
            
        if action == 'approve':
            transfer.status = 'approved'
            transfer.accounting_approver = request.user
        elif action == 'reject':
            transfer.status = 'rejected'
            transfer.accounting_approver = request.user
            if request.method == 'POST':
                transfer.reject_reason = request.POST.get('reject_reason', '')
            
    transfer.save()
    return redirect('assets_system:transfer_list')

@login_required
def approve_disposal(request, disposal_id, action):
    disposal = get_object_or_404(AssetDisposal, pk=disposal_id)
    position_name = request.user.position.name if hasattr(request.user, 'position') and request.user.position else ''
    is_superuser = request.user.is_superuser

    if disposal.status == 'pending_head':
        if not (position_name == 'ผู้จัดการ' or is_superuser):
            messages.error(request, 'คุณไม่มีสิทธิ์อนุมัติรายการนี้')
            return redirect('assets_system:disposal_list')
        
        if action == 'approve':
            disposal.status = 'pending_accounting'
            disposal.head_approver = request.user
        elif action == 'reject':
            disposal.status = 'rejected'
            disposal.head_approver = request.user
            if request.method == 'POST':
                disposal.reject_reason = request.POST.get('reject_reason', '')
            
    elif disposal.status == 'pending_accounting':
        if not (position_name == 'บัญชี' or is_superuser):
            messages.error(request, 'คุณไม่มีสิทธิ์อนุมัติรายการนี้')
            return redirect('assets_system:disposal_list')
            
        if action == 'approve':
            disposal.status = 'approved'
            disposal.accounting_approver = request.user
            asset = disposal.asset
            asset.status = 'disposed'
            asset.save()
        elif action == 'reject':
            disposal.status = 'rejected'
            disposal.accounting_approver = request.user
            if request.method == 'POST':
                disposal.reject_reason = request.POST.get('reject_reason', '')
            
    disposal.save()
    return redirect('assets_system:disposal_list')

@login_required
def fetch_ax_assets(request):
    try:
        conn = pymssql.connect(
            server='173.16.200.32',
            user='FA_report',
            password='F@_report2026',
            database='TLPH',
            charset='utf8'
        )
        cursor = conn.cursor(as_dict=True)
        
        query = """
        SELECT DISTINCT
        ASSETGROUP.GROUPID,
        ASSETTABLE.ASSETID,
        ASSETTABLE.NAME,
        CASE
            WHEN ASSETTABLE.DATAAREAID = 'eatl' THEN N'บริษัท โรงพยาบาลสัตว์เอื้ออารีย์ ทีแอล จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'tltp' THEN N'บริษัท โรงพยาบาลสัตว์ทองหล่อ จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'pptl' THEN N'บริษัท โรงพยาบาลสัตว์เพื่อพูน ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'moya' THEN N'บริษัท โมยา เพ็ทแคร์ จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'sitl' THEN N'บริษัท ศิรินครินทร์ เพ็ท ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'astl' THEN N'บริษัท เอเอสเอ็กซ์ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'tutl' THEN N'บริษัท ทียูทีแอล เพ็ท จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'kstl' THEN N'บริษัท โรงพยาบาลสัตว์ กรุงศรีทีแอล จำกัด'
            ELSE NULL 
        END AS COMPANY,
        CASE 
            WHEN ASSETTABLE.DATAAREAID = 'eatl' THEN 'EA'
            WHEN ASSETTABLE.DATAAREAID = 'tltp' THEN 'TP'
            WHEN ASSETTABLE.DATAAREAID = 'pptl' THEN 'PP'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'JK' THEN 'MY-JK'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'BP' THEN 'MY-BP'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'BM' THEN 'MY-BM'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'PN' THEN 'MY-PN'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'SK' THEN 'MY-SK'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'PU' THEN 'MY-PU'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'NM' THEN 'MY-NM'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'MR' THEN 'MY-MR'
            WHEN ASSETTABLE.DATAAREAID = 'kstl' THEN 'KS'
            WHEN ASSETTABLE.DATAAREAID = 'sitl' THEN 'SI'
            WHEN ASSETTABLE.DATAAREAID = 'astl' THEN 'AS'
            WHEN ASSETTABLE.DATAAREAID = 'tutl' THEN 'TT'
            ELSE NULL 
        END AS BRANCH,
        ASSETTABLE.LOCATIONMEMO AS DEPT,
        CASE
            WHEN ASSETTABLE.LOCATION LIKE 'TP-%' THEN NULL
            WHEN ASSETLOCATION.DATAAREAID LIKE 'kstl' THEN NULL
            ELSE SUBSTRING(ASSETTABLE.LOCATION,3, 2) 
        END AS BUILDING,
        CASE
            WHEN ASSETTABLE.LOCATION LIKE 'TP-%' THEN ASSETLOCATION.NAME
            WHEN ASSETLOCATION.DATAAREAID LIKE 'kstl' THEN NULL
            ELSE SUBSTRING(ASSETTABLE.LOCATION,5, 2) 
        END AS FLOOR,
        ASSETTABLE.ROOMNUMBER,
        ASSETTABLE.SERIALNUM,

        CAST(ASSETTABLE.UNITCOST AS DECIMAL(18, 2)) AS UNITCOST,

        ASSETTABLE.CREATEDDATETIME,
        ASSETTABLE.MAINTENANCEINFO1 AS SUPPLIER,
        CASE 
            WHEN ASSETTABLE.POLICYEXPIRATION = '1900-01-01 00:00:00.000' THEN NULL 
            ELSE ASSETTABLE.POLICYEXPIRATION 
        END AS WARRANTY,
        CASE
            WHEN ASSETGROUP.GROUPID IN ('AS-CO', 'AS-SW', 'EA-CO', 'EA-SW', 'COMP', 'KS-CO', 'KS-SW', 'MY-CO', 'MY-SW', 'PP-CO', 'PP-SW', 'SI-CO', 'SI-SW', 'SW', 'TP-CO', 'TP-SW', 'TT-CO', 'TT-SW') THEN N'หน่วยช่าง IT'
            WHEN ASSETGROUP.GROUPID IN ('AS-MT', 'EA-MT', 'KS-MT', 'MY-MT', 'PP-MT', 'SI-MT', 'TP-MT', 'TT-MT') THEN N'หน่วยช่างเครื่องมือแพทย์'
            WHEN ASSETGROUP.GROUPID IN ('AS-BB', 'AS-BD', 'AS-BDI', 'AS-BIL', 'AS-FU', 'AS-TL', 'AS-VE', 'AS01', 'BB', 'BD', 'BD-LEASE', 'BD40', 'BDI', 'BDI30', 'BDI40', 'BIO', 'BIO10', 'BL', 'COMNU', 'EA-BB', 'EA-BD', 'EA-BDI', 'EA-COMNU', 'EA-FU', 'EA-PP-INS', 'EA-TL', 'EA-VE', 'HO', 'KS-BB', 'KS-BD', 'KS-BDI', 'KS-COMNU', 'KS-FU', 'KS-PP-INS', 'KS-TL', 'KS-VE', 'LD', 'LDI', 'MY-BB', 'MY-BD', 'MY-BDI', 'MY-BIL', 'MY-FU', 'MY-TL', 'MY-VE', 'OFF', 'PP-BB', 'PP-BD', 'PP-BDI', 'PP-FU', 'PP-INS', 'PP-TL', 'PP-VE', 'ROU', 'SI-BB', 'SI-BD', 'SI-BDI', 'SI-FU', 'SI-TL', 'SI-VE', 'TL', 'TL3Y', 'TP-BB', 'TP-BD', 'TP-BD-LEAS', 'TP-BDI', 'TP-COMNU', 'TP-FU', 'TP-LD', 'TP-LDI', 'TP-PP-INS', 'TP-ROU', 'TP-TL', 'TP-VE', 'TT-BB', 'TT-BD', 'TT-BDI', 'TT-BIL', 'TT-COMMU', 'TT-FU', 'TT-TL', 'TT-VE', 'VE') THEN N'หน่วยช่างอาคารและสถานที่'
            ELSE NULL 
        END AS TECH_GROUP,
        ASSETBOOK.STATUS,
        ASSETTABLE.MAINTENANCEINFO3 AS REASON
        FROM ASSETTABLE
        LEFT JOIN ASSETGROUP ON ASSETGROUP.GROUPID = ASSETTABLE.ASSETGROUP AND ASSETGROUP.DATAAREAID = ASSETTABLE.DATAAREAID
        LEFT JOIN ASSETLOCATION ON ASSETLOCATION.LOCATION = ASSETTABLE.LOCATION AND ASSETLOCATION.DATAAREAID = ASSETTABLE.DATAAREAID
        LEFT JOIN ASSETBOOK ON ASSETTABLE.ASSETID = ASSETBOOK.ASSETID AND ASSETBOOK.DATAAREAID = ASSETTABLE.DATAAREAID
        WHERE ASSETTABLE.CREATEDDATETIME >= '2026-05-01'
        AND ASSETTABLE.DATAAREAID NOT LIKE 'tlp%'
        ORDER BY ASSETTABLE.CREATEDDATETIME, ASSETTABLE.ASSETID
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        # Get existing assets using composite keys
        existing_records = set(MasterAsset.objects.values_list('category', 'asset_code', 'branch'))
        seen_in_fetch = set()

        new_assets = []
        for row in rows:
            asset_code = row.get('ASSETID')
            if not asset_code:
                continue
                
            composite_key = (
                str(row.get('GROUPID'))[:255] if row.get('GROUPID') else None,
                str(asset_code)[:50] if asset_code else "-",
                str(row.get('BRANCH'))[:100] if row.get('BRANCH') else None,
            )
            
            if composite_key not in existing_records and composite_key not in seen_in_fetch:
                seen_in_fetch.add(composite_key)
                new_assets.append({
                    'category': row.get('GROUPID'),
                    'asset_code': asset_code,
                    'name': row.get('NAME'),
                    'company': row.get('COMPANY'),
                    'branch': row.get('BRANCH'),
                    'department': row.get('DEPT'),
                    'building': row.get('BUILDING'),
                    'floor': row.get('FLOOR'),
                    'responsible_person': row.get('ROOMNUMBER'),
                    'serial_number': row.get('SERIALNUM'),
                    'price': str(row.get('UNITCOST')) if row.get('UNITCOST') is not None else None,
                    'purchase_date': row.get('CREATEDDATETIME').strftime('%Y-%m-%d %H:%M:%S') if row.get('CREATEDDATETIME') else None,
                    'supplier': row.get('SUPPLIER'),
                    'warranty': row.get('WARRANTY').strftime('%Y-%m-%d %H:%M:%S') if row.get('WARRANTY') else None,
                    'maintenance_unit': row.get('TECH_GROUP'),
                    'ax_status': row.get('STATUS'),
                    'ax_reason': row.get('REASON')
                })
                
        return JsonResponse({'status': 'success', 'data': new_assets})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def sync_ax_assets(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            assets_to_create = []
            seen_in_sync = set()
            
            for item in data.get('assets', []):
                asset_code = item.get('asset_code')
                if not asset_code:
                    continue
                    
                composite_key = (
                    str(item.get('category'))[:255] if item.get('category') else None,
                    str(asset_code)[:50] if asset_code else "-",
                    str(item.get('branch'))[:100] if item.get('branch') else None,
                )
                
                # Double check to prevent duplicates
                if composite_key not in seen_in_sync and not MasterAsset.objects.filter(
                    category=composite_key[0],
                    asset_code=composite_key[1],
                    branch=composite_key[2]
                ).exists():
                    seen_in_sync.add(composite_key)
                    assets_to_create.append(MasterAsset(
                        category=str(item.get('category'))[:255] if item.get('category') else None,
                        asset_code=str(item.get('asset_code'))[:50] if item.get('asset_code') else "-",
                        name=str(item.get('name'))[:255] if item.get('name') else "-",
                        company=str(item.get('company'))[:100] if item.get('company') else None,
                        branch=str(item.get('branch'))[:100] if item.get('branch') else None,
                        department=str(item.get('department'))[:100] if item.get('department') else None,
                        building=str(item.get('building'))[:100] if item.get('building') else None,
                        floor=str(item.get('floor'))[:50] if item.get('floor') else None,
                        responsible_person=str(item.get('responsible_person'))[:200] if item.get('responsible_person') else None,
                        serial_number=str(item.get('serial_number'))[:100] if item.get('serial_number') else None,
                        price=item.get('price') if item.get('price') else None,
                        purchase_date=item.get('purchase_date') or None,
                        supplier=str(item.get('supplier'))[:255] if item.get('supplier') else None,
                        warranty=item.get('warranty') or None,
                        maintenance_unit=str(item.get('maintenance_unit'))[:100] if item.get('maintenance_unit') else None,
                        ax_status=item.get('ax_status'),
                        ax_reason=item.get('ax_reason'),
                        status='available' # Set default status
                    ))
            
            if assets_to_create:
                MasterAsset.objects.bulk_create(assets_to_create)
                messages.success(request, f'นำเข้าข้อมูล Asset จำนวน {len(assets_to_create)} รายการเรียบร้อยแล้ว')
            else:
                messages.warning(request, 'ไม่มีข้อมูล Asset ใหม่ที่ต้องนำเข้า')
                
            return JsonResponse({'status': 'success', 'count': len(assets_to_create)})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required
def fetch_ax_updates(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        site = request.GET.get('site')
        
        if not start_date or not end_date:
            return JsonResponse({'status': 'error', 'message': 'Missing required parameters'}, status=400)
            
        conn = pymssql.connect(
            server='173.16.200.32',
            user='FA_report',
            password='F@_report2026',
            database='TLPH',
            charset='utf8'
        )
        cursor = conn.cursor(as_dict=True)
        
        query = """
        SELECT DISTINCT
        ASSETGROUP.GROUPID,
        ASSETTABLE.ASSETID,
        ASSETTABLE.NAME,
        CASE
            WHEN ASSETTABLE.DATAAREAID = 'eatl' THEN N'บริษัท โรงพยาบาลสัตว์เอื้ออารีย์ ทีแอล จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'tltp' THEN N'บริษัท โรงพยาบาลสัตว์ทองหล่อ จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'pptl' THEN N'บริษัท โรงพยาบาลสัตว์เพื่อพูน ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'moya' THEN N'บริษัท โมยา เพ็ทแคร์ จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'sitl' THEN N'บริษัท ศิรินครินทร์ เพ็ท ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'astl' THEN N'บริษัท เอเอสเอ็กซ์ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'tutl' THEN N'บริษัท ทียูทีแอล เพ็ท จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'kstl' THEN N'บริษัท โรงพยาบาลสัตว์ กรุงศรีทีแอล จำกัด'
            ELSE NULL 
        END AS COMPANY,
        CASE 
            WHEN ASSETTABLE.DATAAREAID = 'eatl' THEN 'EA'
            WHEN ASSETTABLE.DATAAREAID = 'tltp' THEN 'TP'
            WHEN ASSETTABLE.DATAAREAID = 'pptl' THEN 'PP'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'JK' THEN 'MY-JK'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'BP' THEN 'MY-BP'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'BM' THEN 'MY-BM'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'PN' THEN 'MY-PN'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'SK' THEN 'MY-SK'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'PU' THEN 'MY-PU'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'NM' THEN 'MY-NM'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'MR' THEN 'MY-MR'
            WHEN ASSETTABLE.DATAAREAID = 'kstl' THEN 'KS'
            WHEN ASSETTABLE.DATAAREAID = 'sitl' THEN 'SI'
            WHEN ASSETTABLE.DATAAREAID = 'astl' THEN 'AS'
            WHEN ASSETTABLE.DATAAREAID = 'tutl' THEN 'TT'
            ELSE NULL 
        END AS BRANCH,
        ASSETTABLE.LOCATIONMEMO AS DEPT,
        CASE
            WHEN ASSETTABLE.LOCATION LIKE 'TP-%' THEN NULL
            WHEN ASSETLOCATION.DATAAREAID LIKE 'kstl' THEN NULL
            ELSE SUBSTRING(ASSETTABLE.LOCATION,3, 2) 
        END AS BUILDING,
        CASE
            WHEN ASSETTABLE.LOCATION LIKE 'TP-%' THEN ASSETLOCATION.NAME
            WHEN ASSETLOCATION.DATAAREAID LIKE 'kstl' THEN NULL
            ELSE SUBSTRING(ASSETTABLE.LOCATION,5, 2) 
        END AS FLOOR,
        ASSETTABLE.ROOMNUMBER,
        ASSETTABLE.SERIALNUM,
        CAST(ASSETTABLE.UNITCOST AS DECIMAL(18, 2)) AS UNITCOST,
        ASSETTABLE.CREATEDDATETIME,
        ASSETTABLE.MAINTENANCEINFO1 AS SUPPLIER,
        CASE 
            WHEN ASSETTABLE.POLICYEXPIRATION = '1900-01-01 00:00:00.000' THEN NULL 
            ELSE ASSETTABLE.POLICYEXPIRATION 
        END AS WARRANTY,
        CASE
            WHEN ASSETGROUP.GROUPID IN ('AS-CO', 'AS-SW', 'EA-CO', 'EA-SW', 'COMP', 'KS-CO', 'KS-SW', 'MY-CO', 'MY-SW', 'PP-CO', 'PP-SW', 'SI-CO', 'SI-SW', 'SW', 'TP-CO', 'TP-SW', 'TT-CO', 'TT-SW') THEN N'หน่วยช่าง IT'
            WHEN ASSETGROUP.GROUPID IN ('AS-MT', 'EA-MT', 'KS-MT', 'MY-MT', 'PP-MT', 'SI-MT', 'TP-MT', 'TT-MT') THEN N'หน่วยช่างเครื่องมือแพทย์'
            WHEN ASSETGROUP.GROUPID IN ('AS-BB', 'AS-BD', 'AS-BDI', 'AS-BIL', 'AS-FU', 'AS-TL', 'AS-VE', 'AS01', 'BB', 'BD', 'BD-LEASE', 'BD40', 'BDI', 'BDI30', 'BDI40', 'BIO', 'BIO10', 'BL', 'COMNU', 'EA-BB', 'EA-BD', 'EA-BDI', 'EA-COMNU', 'EA-FU', 'EA-PP-INS', 'EA-TL', 'EA-VE', 'HO', 'KS-BB', 'KS-BD', 'KS-BDI', 'KS-COMNU', 'KS-FU', 'KS-PP-INS', 'KS-TL', 'KS-VE', 'LD', 'LDI', 'MY-BB', 'MY-BD', 'MY-BDI', 'MY-BIL', 'MY-FU', 'MY-TL', 'MY-VE', 'OFF', 'PP-BB', 'PP-BD', 'PP-BDI', 'PP-FU', 'PP-INS', 'PP-TL', 'PP-VE', 'ROU', 'SI-BB', 'SI-BD', 'SI-BDI', 'SI-FU', 'SI-TL', 'SI-VE', 'TL', 'TL3Y', 'TP-BB', 'TP-BD', 'TP-BD-LEAS', 'TP-BDI', 'TP-COMNU', 'TP-FU', 'TP-LD', 'TP-LDI', 'TP-PP-INS', 'TP-ROU', 'TP-TL', 'TP-VE', 'TT-BB', 'TT-BD', 'TT-BDI', 'TT-BIL', 'TT-COMMU', 'TT-FU', 'TT-TL', 'TT-VE', 'VE') THEN N'หน่วยช่างอาคารและสถานที่'
            ELSE NULL 
        END AS TECH_GROUP,
        ASSETBOOK.STATUS,
        ASSETTABLE.MAINTENANCEINFO3 AS REASON
        FROM ASSETTABLE
        LEFT JOIN ASSETGROUP ON ASSETGROUP.GROUPID = ASSETTABLE.ASSETGROUP AND ASSETGROUP.DATAAREAID = ASSETTABLE.DATAAREAID
        LEFT JOIN ASSETLOCATION ON ASSETLOCATION.LOCATION = ASSETTABLE.LOCATION AND ASSETLOCATION.DATAAREAID = ASSETTABLE.DATAAREAID
        LEFT JOIN ASSETBOOK ON ASSETTABLE.ASSETID = ASSETBOOK.ASSETID AND ASSETBOOK.DATAAREAID = ASSETTABLE.DATAAREAID
        WHERE ASSETTABLE.MODIFIEDDATETIME BETWEEN %s AND %s
        AND ASSETTABLE.DATAAREAID NOT LIKE 'tlp%'
        """
        
        query_params = [start_date, f"{end_date} 23:59:59"]
        
        if site:
            query += " AND ASSETTABLE.DATAAREAID = %s"
            query_params.append(site)
            
        query += "\nORDER BY ASSETTABLE.CREATEDDATETIME, ASSETTABLE.ASSETID"

        cursor.execute(query, tuple(query_params))
        rows = cursor.fetchall()
        conn.close()

        # Load all assets into memory for matching (O(N) vs O(N^2) DB queries)
        local_assets_qs = MasterAsset.objects.all()
        # Dictionary to look up assets by composite key: (category, asset_code, branch)
        local_assets_map = {}
        for a in local_assets_qs:
            key = (
                str(a.category)[:255] if a.category else None,
                str(a.asset_code)[:50] if a.asset_code else "-",
                str(a.branch)[:100] if a.branch else None,
            )
            local_assets_map[key] = a
        
        updated_assets = []
        seen_in_fetch = set()

        for row in rows:
            asset_code = row.get('ASSETID')
            if not asset_code:
                continue
                
            composite_key = (
                str(row.get('GROUPID'))[:255] if row.get('GROUPID') else None,
                str(asset_code)[:50] if asset_code else "-",
                str(row.get('BRANCH'))[:100] if row.get('BRANCH') else None,
            )
            
            # We only care about assets that already exist in our DB
            if composite_key in local_assets_map and composite_key not in seen_in_fetch:
                seen_in_fetch.add(composite_key)
                local_asset = local_assets_map[composite_key]
                
                # Check for changes in mapped fields
                # Mapping of field_name to expected value from AX
                ax_data = {
                    'name': str(row.get('NAME'))[:255] if row.get('NAME') else "-",
                    'company': str(row.get('COMPANY'))[:100] if row.get('COMPANY') else None,
                    'department': str(row.get('DEPT'))[:100] if row.get('DEPT') else None,
                    'building': str(row.get('BUILDING'))[:100] if row.get('BUILDING') else None,
                    'floor': str(row.get('FLOOR'))[:50] if row.get('FLOOR') else None,
                    'responsible_person': str(row.get('ROOMNUMBER'))[:200] if row.get('ROOMNUMBER') else None,
                    'serial_number': str(row.get('SERIALNUM'))[:100] if row.get('SERIALNUM') else None,
                    'price': str(row.get('UNITCOST')) if row.get('UNITCOST') is not None else None,
                    'supplier': str(row.get('SUPPLIER'))[:255] if row.get('SUPPLIER') else None,
                    'maintenance_unit': str(row.get('TECH_GROUP'))[:100] if row.get('TECH_GROUP') else None,
                    'ax_status': row.get('STATUS'),
                    'ax_reason': row.get('REASON')
                }
                
                changes = {}
                # Compare each mapped field
                if str(local_asset.name or None) != str(ax_data['name'] or None):
                    changes['name'] = {'old': local_asset.name, 'new': ax_data['name']}
                if str(local_asset.company or None) != str(ax_data['company'] or None):
                    changes['company'] = {'old': local_asset.company, 'new': ax_data['company']}
                if str(local_asset.department or None) != str(ax_data['department'] or None):
                    changes['department'] = {'old': local_asset.department, 'new': ax_data['department']}
                if str(local_asset.building or None) != str(ax_data['building'] or None):
                    changes['building'] = {'old': local_asset.building, 'new': ax_data['building']}
                if str(local_asset.floor or None) != str(ax_data['floor'] or None):
                    changes['floor'] = {'old': local_asset.floor, 'new': ax_data['floor']}
                if str(local_asset.responsible_person or None) != str(ax_data['responsible_person'] or None):
                    changes['responsible_person'] = {'old': local_asset.responsible_person, 'new': ax_data['responsible_person']}
                if str(local_asset.serial_number or None) != str(ax_data['serial_number'] or None):
                    changes['serial_number'] = {'old': local_asset.serial_number, 'new': ax_data['serial_number']}
                
                # Decimal comparison is tricky, so compare string representations (ignoring trailing zeros if needed)
                local_price_str = f"{local_asset.price:.2f}" if local_asset.price is not None else None
                ax_price_str = f"{float(ax_data['price']):.2f}" if ax_data['price'] else None
                if local_price_str != ax_price_str:
                    changes['price'] = {'old': local_price_str, 'new': ax_data['price']}
                    
                if str(local_asset.supplier or None) != str(ax_data['supplier'] or None):
                    changes['supplier'] = {'old': local_asset.supplier, 'new': ax_data['supplier']}
                if str(local_asset.maintenance_unit or None) != str(ax_data['maintenance_unit'] or None):
                    changes['maintenance_unit'] = {'old': local_asset.maintenance_unit, 'new': ax_data['maintenance_unit']}
                if str(local_asset.ax_status or None) != str(ax_data['ax_status'] or None):
                    changes['ax_status'] = {'old': local_asset.ax_status, 'new': ax_data['ax_status']}
                if str(local_asset.ax_reason or None) != str(ax_data['ax_reason'] or None):
                    changes['ax_reason'] = {'old': local_asset.ax_reason, 'new': ax_data['ax_reason']}

                # Compare purchase_date and warranty separately
                local_pdate = local_asset.purchase_date.strftime('%Y-%m-%d %H:%M:%S') if local_asset.purchase_date else None
                ax_pdate = row.get('CREATEDDATETIME').strftime('%Y-%m-%d %H:%M:%S') if row.get('CREATEDDATETIME') else None
                if local_pdate != ax_pdate:
                    changes['purchase_date'] = {'old': local_pdate, 'new': ax_pdate}
                    
                local_wdate = local_asset.warranty.strftime('%Y-%m-%d %H:%M:%S') if local_asset.warranty else None
                ax_wdate = row.get('WARRANTY').strftime('%Y-%m-%d %H:%M:%S') if row.get('WARRANTY') else None
                if local_wdate != ax_wdate:
                    changes['warranty'] = {'old': local_wdate, 'new': ax_wdate}
                
                if changes:
                    # If there's any change, package it up
                    updated_assets.append({
                        'category': composite_key[0],
                        'asset_code': composite_key[1],
                        'name': local_asset.name,
                        'branch': composite_key[2],
                        'changes': changes,
                        'full_data': {
                            'category': composite_key[0],
                            'asset_code': composite_key[1],
                            'name': ax_data['name'],
                            'company': ax_data['company'],
                            'branch': composite_key[2],
                            'department': ax_data['department'],
                            'building': ax_data['building'],
                            'floor': ax_data['floor'],
                            'responsible_person': ax_data['responsible_person'],
                            'serial_number': ax_data['serial_number'],
                            'price': ax_data['price'],
                            'purchase_date': ax_pdate,
                            'supplier': ax_data['supplier'],
                            'warranty': ax_wdate,
                            'maintenance_unit': ax_data['maintenance_unit'],
                            'ax_status': ax_data['ax_status'],
                            'ax_reason': ax_data['ax_reason']
                        }
                    })
                
        return JsonResponse({'status': 'success', 'data': updated_assets})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def apply_ax_updates(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            updates_to_apply = data.get('assets', [])
            count = 0
            
            for item in updates_to_apply:
                composite_key = (
                    str(item.get('category'))[:255] if item.get('category') else None,
                    str(item.get('asset_code'))[:50] if item.get('asset_code') else "-",
                    str(item.get('branch'))[:100] if item.get('branch') else None,
                )
                
                # Fetch local asset by composite key
                local_asset = MasterAsset.objects.filter(
                    category=composite_key[0],
                    asset_code=composite_key[1],
                    branch=composite_key[2]
                ).first()
                
                if local_asset:
                    changes = item.get('changes', {})
                    for field, change_data in changes.items():
                        new_value = change_data.get('new') if isinstance(change_data, dict) else change_data
                        if field in ['purchase_date', 'warranty']:
                            setattr(local_asset, field, new_value or None)
                        elif field == 'price':
                            setattr(local_asset, field, new_value if new_value is not None else None)
                        else:
                            setattr(local_asset, field, new_value)
                    local_asset.save()
                    count += 1
            
            if count > 0:
                messages.success(request, f'อัปเดตข้อมูล Asset จำนวน {count} รายการเรียบร้อยแล้ว')
            else:
                messages.warning(request, 'ไม่มีข้อมูล Asset ถูกอัปเดต')
                
            return JsonResponse({'status': 'success', 'count': count})
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@login_required
def sync_single_ax_asset(request, asset_id):
    try:
        # 1. Fetch the local asset
        local_asset = get_object_or_404(MasterAsset, pk=asset_id)
        
        if not local_asset.asset_code or local_asset.asset_code == "-":
            return JsonResponse({'status': 'error', 'message': 'Asset นี้ไม่มีรหัสทรัพย์สิน (Asset Code) ที่สมบูรณ์'}, status=400)
            
        # Composite key for this local asset
        local_key = (
            str(local_asset.category)[:255] if local_asset.category else None,
            str(local_asset.asset_code)[:50] if local_asset.asset_code else "-",
            str(local_asset.branch)[:100] if local_asset.branch else None,
        )

        # 2. Connect to AX DB
        conn = pymssql.connect(
            server='173.16.200.32',
            user='FA_report',
            password='F@_report2026',
            database='TLPH',
            charset='utf8'
        )
        cursor = conn.cursor(as_dict=True)
        
        # 3. Query AX for this specific asset_code
        query = """
        SELECT DISTINCT
        ASSETGROUP.GROUPID,
        ASSETTABLE.ASSETID,
        ASSETTABLE.NAME,
        CASE
            WHEN ASSETTABLE.DATAAREAID = 'eatl' THEN N'บริษัท โรงพยาบาลสัตว์เอื้ออารีย์ ทีแอล จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'tltp' THEN N'บริษัท โรงพยาบาลสัตว์ทองหล่อ จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'pptl' THEN N'บริษัท โรงพยาบาลสัตว์เพื่อพูน ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'moya' THEN N'บริษัท โมยา เพ็ทแคร์ จํากัด'
            WHEN ASSETTABLE.DATAAREAID = 'sitl' THEN N'บริษัท ศิรินครินทร์ เพ็ท ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'astl' THEN N'บริษัท เอเอสเอ็กซ์ทีแอล จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'tutl' THEN N'บริษัท ทียูทีแอล เพ็ท จำกัด'
            WHEN ASSETTABLE.DATAAREAID = 'kstl' THEN N'บริษัท โรงพยาบาลสัตว์ กรุงศรีทีแอล จำกัด'
            ELSE NULL 
        END AS COMPANY,
        CASE 
            WHEN ASSETTABLE.DATAAREAID = 'eatl' THEN 'EA'
            WHEN ASSETTABLE.DATAAREAID = 'tltp' THEN 'TP'
            WHEN ASSETTABLE.DATAAREAID = 'pptl' THEN 'PP'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'JK' THEN 'MY-JK'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'BP' THEN 'MY-BP'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'BM' THEN 'MY-BM'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'PN' THEN 'MY-PN'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'SK' THEN 'MY-SK'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'PU' THEN 'MY-PU'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'NM' THEN 'MY-NM'
            WHEN ASSETTABLE.DATAAREAID = 'moya' AND SUBSTRING(ASSETTABLE.LOCATION,1, 2) = 'MR' THEN 'MY-MR'
            WHEN ASSETTABLE.DATAAREAID = 'kstl' THEN 'KS'
            WHEN ASSETTABLE.DATAAREAID = 'sitl' THEN 'SI'
            WHEN ASSETTABLE.DATAAREAID = 'astl' THEN 'AS'
            WHEN ASSETTABLE.DATAAREAID = 'tutl' THEN 'TT'
            ELSE NULL 
        END AS BRANCH,
        ASSETTABLE.LOCATIONMEMO AS DEPT,
        CASE
            WHEN ASSETTABLE.LOCATION LIKE 'TP-%' THEN NULL
            WHEN ASSETLOCATION.DATAAREAID LIKE 'kstl' THEN NULL
            ELSE SUBSTRING(ASSETTABLE.LOCATION,3, 2) 
        END AS BUILDING,
        CASE
            WHEN ASSETTABLE.LOCATION LIKE 'TP-%' THEN ASSETLOCATION.NAME
            WHEN ASSETLOCATION.DATAAREAID LIKE 'kstl' THEN NULL
            ELSE SUBSTRING(ASSETTABLE.LOCATION,5, 2) 
        END AS FLOOR,
        ASSETTABLE.ROOMNUMBER,
        ASSETTABLE.SERIALNUM,
        CAST(ASSETTABLE.UNITCOST AS DECIMAL(18, 2)) AS UNITCOST,
        ASSETTABLE.CREATEDDATETIME,
        ASSETTABLE.MAINTENANCEINFO1 AS SUPPLIER,
        CASE 
            WHEN ASSETTABLE.POLICYEXPIRATION = '1900-01-01 00:00:00.000' THEN NULL 
            ELSE ASSETTABLE.POLICYEXPIRATION 
        END AS WARRANTY,
        CASE
            WHEN ASSETGROUP.GROUPID IN ('AS-CO', 'AS-SW', 'EA-CO', 'EA-SW', 'COMP', 'KS-CO', 'KS-SW', 'MY-CO', 'MY-SW', 'PP-CO', 'PP-SW', 'SI-CO', 'SI-SW', 'SW', 'TP-CO', 'TP-SW', 'TT-CO', 'TT-SW') THEN N'หน่วยช่าง IT'
            WHEN ASSETGROUP.GROUPID IN ('AS-MT', 'EA-MT', 'KS-MT', 'MY-MT', 'PP-MT', 'SI-MT', 'TP-MT', 'TT-MT') THEN N'หน่วยช่างเครื่องมือแพทย์'
            WHEN ASSETGROUP.GROUPID IN ('AS-BB', 'AS-BD', 'AS-BDI', 'AS-BIL', 'AS-FU', 'AS-TL', 'AS-VE', 'AS01', 'BB', 'BD', 'BD-LEASE', 'BD40', 'BDI', 'BDI30', 'BDI40', 'BIO', 'BIO10', 'BL', 'COMNU', 'EA-BB', 'EA-BD', 'EA-BDI', 'EA-COMNU', 'EA-FU', 'EA-PP-INS', 'EA-TL', 'EA-VE', 'HO', 'KS-BB', 'KS-BD', 'KS-BDI', 'KS-COMNU', 'KS-FU', 'KS-PP-INS', 'KS-TL', 'KS-VE', 'LD', 'LDI', 'MY-BB', 'MY-BD', 'MY-BDI', 'MY-BIL', 'MY-FU', 'MY-TL', 'MY-VE', 'OFF', 'PP-BB', 'PP-BD', 'PP-BDI', 'PP-FU', 'PP-INS', 'PP-TL', 'PP-VE', 'ROU', 'SI-BB', 'SI-BD', 'SI-BDI', 'SI-FU', 'SI-TL', 'SI-VE', 'TL', 'TL3Y', 'TP-BB', 'TP-BD', 'TP-BD-LEAS', 'TP-BDI', 'TP-COMNU', 'TP-FU', 'TP-LD', 'TP-LDI', 'TP-PP-INS', 'TP-ROU', 'TP-TL', 'TP-VE', 'TT-BB', 'TT-BD', 'TT-BDI', 'TT-BIL', 'TT-COMMU', 'TT-FU', 'TT-TL', 'TT-VE', 'VE') THEN N'หน่วยช่างอาคารและสถานที่'
            ELSE NULL 
        END AS TECH_GROUP,
        ASSETBOOK.STATUS,
        ASSETTABLE.MAINTENANCEINFO3 AS REASON
        FROM ASSETTABLE
        LEFT JOIN ASSETGROUP ON ASSETGROUP.GROUPID = ASSETTABLE.ASSETGROUP AND ASSETGROUP.DATAAREAID = ASSETTABLE.DATAAREAID
        LEFT JOIN ASSETLOCATION ON ASSETLOCATION.LOCATION = ASSETTABLE.LOCATION AND ASSETLOCATION.DATAAREAID = ASSETTABLE.DATAAREAID
        LEFT JOIN ASSETBOOK ON ASSETTABLE.ASSETID = ASSETBOOK.ASSETID AND ASSETBOOK.DATAAREAID = ASSETTABLE.DATAAREAID
        WHERE ASSETTABLE.DATAAREAID NOT LIKE 'tlp%'
        AND ASSETTABLE.ASSETID = %s
        ORDER BY ASSETTABLE.CREATEDDATETIME, ASSETTABLE.ASSETID
        """
        
        cursor.execute(query, (local_asset.asset_code,))
        rows = cursor.fetchall()
        conn.close()

        has_changes = False
        
        for row in rows:
            ax_key = (
                str(row.get('GROUPID'))[:255] if row.get('GROUPID') else None,
                str(row.get('ASSETID'))[:50] if row.get('ASSETID') else "-",
                str(row.get('BRANCH'))[:100] if row.get('BRANCH') else None,
            )
            
            if ax_key == local_key:
                ax_data = {
                    'name': str(row.get('NAME'))[:255] if row.get('NAME') else "-",
                    'company': str(row.get('COMPANY'))[:100] if row.get('COMPANY') else None,
                    'department': str(row.get('DEPT'))[:100] if row.get('DEPT') else None,
                    'building': str(row.get('BUILDING'))[:100] if row.get('BUILDING') else None,
                    'floor': str(row.get('FLOOR'))[:50] if row.get('FLOOR') else None,
                    'responsible_person': str(row.get('ROOMNUMBER'))[:200] if row.get('ROOMNUMBER') else None,
                    'serial_number': str(row.get('SERIALNUM'))[:100] if row.get('SERIALNUM') else None,
                    'price': str(row.get('UNITCOST')) if row.get('UNITCOST') is not None else None,
                    'supplier': str(row.get('SUPPLIER'))[:255] if row.get('SUPPLIER') else None,
                    'maintenance_unit': str(row.get('TECH_GROUP'))[:100] if row.get('TECH_GROUP') else None,
                    'ax_status': row.get('STATUS'),
                    'ax_reason': row.get('REASON')
                }
                
                # Check for changes in mapped fields
                changes = {}
                if str(local_asset.name or None) != str(ax_data['name'] or None):
                    changes['name'] = {'old': local_asset.name, 'new': ax_data['name']}
                    local_asset.name = ax_data['name']
                    has_changes = True
                if str(local_asset.company or None) != str(ax_data['company'] or None):
                    changes['company'] = {'old': local_asset.company, 'new': ax_data['company']}
                    local_asset.company = ax_data['company']
                    has_changes = True
                if str(local_asset.department or None) != str(ax_data['department'] or None):
                    changes['department'] = {'old': local_asset.department, 'new': ax_data['department']}
                    local_asset.department = ax_data['department']
                    has_changes = True
                if str(local_asset.building or None) != str(ax_data['building'] or None):
                    changes['building'] = {'old': local_asset.building, 'new': ax_data['building']}
                    local_asset.building = ax_data['building']
                    has_changes = True
                if str(local_asset.floor or None) != str(ax_data['floor'] or None):
                    changes['floor'] = {'old': local_asset.floor, 'new': ax_data['floor']}
                    local_asset.floor = ax_data['floor']
                    has_changes = True
                if str(local_asset.responsible_person or None) != str(ax_data['responsible_person'] or None):
                    changes['responsible_person'] = {'old': local_asset.responsible_person, 'new': ax_data['responsible_person']}
                    local_asset.responsible_person = ax_data['responsible_person']
                    has_changes = True
                if str(local_asset.serial_number or None) != str(ax_data['serial_number'] or None):
                    changes['serial_number'] = {'old': local_asset.serial_number, 'new': ax_data['serial_number']}
                    local_asset.serial_number = ax_data['serial_number']
                    has_changes = True
                
                local_price_str = f"{local_asset.price:.2f}" if local_asset.price is not None else None
                ax_price_str = f"{float(ax_data['price']):.2f}" if ax_data['price'] else None
                if local_price_str != ax_price_str:
                    changes['price'] = {'old': local_price_str, 'new': ax_price_str}
                    local_asset.price = ax_data['price']
                    has_changes = True
                    
                if str(local_asset.supplier or None) != str(ax_data['supplier'] or None):
                    changes['supplier'] = {'old': local_asset.supplier, 'new': ax_data['supplier']}
                    local_asset.supplier = ax_data['supplier']
                    has_changes = True
                if str(local_asset.maintenance_unit or None) != str(ax_data['maintenance_unit'] or None):
                    changes['maintenance_unit'] = {'old': local_asset.maintenance_unit, 'new': ax_data['maintenance_unit']}
                    local_asset.maintenance_unit = ax_data['maintenance_unit']
                    has_changes = True
                if str(local_asset.ax_status or None) != str(ax_data['ax_status'] or None):
                    changes['ax_status'] = {'old': local_asset.ax_status, 'new': ax_data['ax_status']}
                    local_asset.ax_status = ax_data['ax_status']
                    has_changes = True
                if str(local_asset.ax_reason or None) != str(ax_data['ax_reason'] or None):
                    changes['ax_reason'] = {'old': local_asset.ax_reason, 'new': ax_data['ax_reason']}
                    local_asset.ax_reason = ax_data['ax_reason']
                    has_changes = True

                local_pdate = local_asset.purchase_date.strftime('%Y-%m-%d %H:%M:%S') if local_asset.purchase_date else None
                ax_pdate = row.get('CREATEDDATETIME').strftime('%Y-%m-%d %H:%M:%S') if row.get('CREATEDDATETIME') else None
                if local_pdate != ax_pdate:
                    changes['purchase_date'] = {'old': local_pdate, 'new': ax_pdate}
                    local_asset.purchase_date = ax_pdate
                    has_changes = True
                    
                local_wdate = local_asset.warranty.strftime('%Y-%m-%d %H:%M:%S') if local_asset.warranty else None
                ax_wdate = row.get('WARRANTY').strftime('%Y-%m-%d %H:%M:%S') if row.get('WARRANTY') else None
                if local_wdate != ax_wdate:
                    changes['warranty'] = {'old': local_wdate, 'new': ax_wdate}
                    local_asset.warranty = ax_wdate
                    has_changes = True
                
                if request.GET.get('dry_run') == 'true':
                    if has_changes:
                        return JsonResponse({'status': 'success', 'has_changes': True, 'changes': changes})
                    else:
                        return JsonResponse({'status': 'success', 'has_changes': False, 'message': 'ไม่พบข้อมูลที่มีการเปลี่ยนแปลงจาก AX'})
                
                if has_changes:
                    local_asset.save()
                    return JsonResponse({'status': 'success', 'message': 'อัพเดทข้อมูลเรียบร้อย', 'updated': True})
                else:
                    return JsonResponse({'status': 'success', 'message': 'ไม่พบข้อมูลอัพเดทจาก ax', 'updated': False})
                    
        # If loop finishes without returning, it means no match was found for the 4-column key
        return JsonResponse({'status': 'success', 'message': 'ไม่พบข้อมูลอัพเดทจาก ax', 'updated': False})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@require_POST
def ajax_add_sub_asset(request, asset_id):
    try:
        master_asset = get_object_or_404(MasterAsset, pk=asset_id)
        
        # Load JSON data
        data = json.loads(request.body)
        name = data.get('name')
        serial_number = data.get('serial_number')
        description = data.get('description')
        
        if not name:
            return JsonResponse({'status': 'error', 'message': 'กรุณาระบุชื่อทรัพย์สินย่อย'}, status=400)
            
        sub_asset = SubAsset.objects.create(
            master_asset=master_asset,
            name=name,
            serial_number=serial_number,
            description=description
        )
        
        return JsonResponse({
            'status': 'success',
            'sub_asset_id': sub_asset.id,
            'sub_asset_name': str(sub_asset)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def ajax_upload_asset_images(request, asset_id):
    try:
        asset = get_object_or_404(MasterAsset, pk=asset_id)
        
        # 1. Handle Cover Image
        if 'cover_image' in request.FILES:
            cover_img = request.FILES['cover_image']
            if cover_img.size > 5 * 1024 * 1024:
                return JsonResponse({'status': 'error', 'message': 'รูปหน้าปกขนาดเกิน 5MB'}, status=400)
                
            # Delete old image if it exists
            if asset.image and os.path.isfile(asset.image.path):
                os.remove(asset.image.path)
                
            asset.image = cover_img
            asset.save()
            
        # 2. Handle Additional Images
        additional_images = request.FILES.getlist('additional_images')
        for img in additional_images:
            if img.size > 5 * 1024 * 1024:
                return JsonResponse({'status': 'error', 'message': f'รูปภาพ {img.name} ขนาดเกิน 5MB'}, status=400)
                
            AssetImage.objects.create(asset=asset, image=img)
            
        return JsonResponse({'status': 'success', 'message': 'อัปโหลดรูปภาพสำเร็จ'})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@require_POST
def ajax_delete_additional_images(request):
    try:
        data = json.loads(request.body)
        image_ids = data.get('image_ids', [])
        
        if not image_ids:
            return JsonResponse({'status': 'error', 'message': 'ไม่พบรูปภาพที่เลือกเพื่อลบ'}, status=400)
            
        images = AssetImage.objects.filter(id__in=image_ids)
        for img in images:
            if img.image and os.path.isfile(img.image.path):
                os.remove(img.image.path)
            img.delete()
            
        return JsonResponse({'status': 'success', 'message': 'ลบรูปภาพที่เลือกสำเร็จ'})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
