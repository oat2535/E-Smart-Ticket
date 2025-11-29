from django.shortcuts import render,redirect
from case.models import Case
from django.contrib.auth.decorators import login_required #import model บังคับต้องให้ login ก่อนเข้าใช้งาน
from django.contrib import auth,messages #import auth
from datetime import datetime, timedelta
from django.utils.encoding import smart_str
import csv
from django.http import HttpResponse
from members.models import Members
from status.models import Status
from branch.models import Branch
from sub_branch.models import SubBranch
from django.db.models import Q
from django.http import JsonResponse
from dateutil.parser import parse as parse_datetime

# Create your views here.

@login_required(login_url="member")
def reportCase(request):
    create_username = auth.get_user(request) #get user ตามที่ login
    user_branch = request.user.branch  # รับข้อมูลสาขาของผู้ใช้ที่ล็อกอิน
    
    # รับค่าจากฟอร์มกรอง
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    assign_name = request.POST.get('assign_name')
    branch_id = request.POST.get('branch_id')
    sub_branch_id = request.POST.get('sub_branch_id')
    status = request.POST.get('status')
    # ตรวจสอบค่าเริ่มต้นของ start_date และ end_date
    cases = Case.objects.all()  # กำหนดค่าเริ่มต้นเป็น queryset ว่าง
    print("assign_name:", assign_name)
    print("status:", status)

    # ตรวจสอบว่า start_date และ end_date ไม่เป็น None
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        start_date = None  # หรือกำหนดค่าเริ่มต้นที่คุณต้องการ

    if end_date:
        original_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()  # เก็บวันที่เดิม
        # เพิ่ม 1 วันให้กับ end_date สำหรับการค้นหา
        end_date = (datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)).date()
    else:
        original_end_date = None  # หรือกำหนดค่าเริ่มต้นที่คุณต้องการ

    # ถ้าไม่เลือกอะไรเลย
    if not (start_date or end_date or assign_name or status or branch_id or sub_branch_id):
        cases = Case.objects.none()

    # กรองข้อมูลในกรณีที่ start_date และ end_date มีค่า
    if start_date and end_date:
        if request.user.username == "admin":
            cases = Case.objects.filter(date_created__gte=start_date, date_created__lt=end_date).order_by('-pk')  # ไม่กรองตามสาขา
        elif request.user.department_id == "IT":
            cases = Case.objects.filter(date_created__gte=start_date, date_created__lt=end_date, department_id="IT").order_by('-pk')  # ไม่กรองตามสาขา  
        elif request.user.department_id == "PUR":
            cases = Case.objects.filter(date_created__gte=start_date, date_created__lt=end_date, department_id="PUR").order_by('-pk')  # ไม่กรองตามสาขา
        elif request.user.department_id == "FIN":
            cases = Case.objects.filter(date_created__gte=start_date, date_created__lt=end_date, department_id="FIN").order_by('-pk')  # ไม่กรองตามสาขา
        else:
            cases = Case.objects.filter(date_created__gte=start_date, date_created__lt=end_date, branch=user_branch).order_by('-pk')   # กรองตามสาขา


      # กรองตาม assign_name ถ้ามีการเลือก
    if assign_name:
        cases = cases.filter(assign_name__username=assign_name)
    
    if status:
        cases = cases.filter(status_id=status)
    
    if branch_id:
        cases = cases.filter(branch_id=branch_id)

    if sub_branch_id:
        cases = cases.filter(sub_branch_id=sub_branch_id)
    
    for case in cases:
        # ดึงข้อมูลจาก model Members โดยใช้ assign_name (username) เทียบกับ Members.username
        try:
            member = Members.objects.get(username=case.assign_name)
            case.assign_name_full = f"{member.first_name} {member.last_name}"  # เก็บชื่อและนามสกุล
        except Members.DoesNotExist:
            case.assign_name_full = ""  # กรณีที่ไม่พบสมาชิก
  
    # ส่งข้อมูลไปยัง Template
    if create_username.is_staff:
    # กรณี user เป็น staff: filter ตาม department_id
        members = Members.objects.filter(
            is_staff=True,
            department_id=create_username.department_id  # สมมุติว่ามี field นี้
        ).exclude(username='admin')
    else:
        # กรณีไม่ใช่ staff: ดึง staff ทั้งหมด
        members = Members.objects.filter(
            is_staff=True
        ).exclude(username='admin')
    status_qs = Status.objects.all().order_by('pk')
    branches = Branch.objects.all().order_by('branch_name')
    sub_branches = SubBranch.objects.all().order_by('sub_branch_name')
    context = {
        'cases': cases,
        'start_date': start_date,
        'end_date': original_end_date,
        'create_username':create_username,
        'members': members,
        'assign_name': assign_name, 
        'status':status_qs,
        'branches': branches,
        'sub_branches': sub_branches,
        'status_selected': status,
        'branch_id': branch_id,             
        'sub_branch_id': sub_branch_id,    
    }
    return render(request, "backend/report.html",context)

def export_csv(request):
    create_username = auth.get_user(request)
    department_id = request.user.department_id
    current_date = datetime.now().strftime('%Y-%m-%d')
    filename = f'caseReport{current_date}.csv'
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(u'\ufeff'.encode('utf-8-sig'))

    writer = csv.writer(response)
    writer.writerow(['รหัสเคส', 'ประเภท', 'กลุ่มงาน', 'กลุ่มงาน(ย่อย)','หัวข้อ', 'รายละเอียด', 'รายละเอียดแก้ไข', 'ผู้แจ้งซ่อม', 
                     'วันที่แจ้ง', 'วันที่รับเคส', 'วันที่ปิดเคส', 'ผู้รับเคส', 'Company', 'สาขา', 'สถานะ', 'คะแนน'])

    # รับค่าตัวกรองจาก GET
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    assign_name = request.GET.get('assign_name')
    status_id = request.GET.get('status')
    branch_id = request.GET.get('branch_id')
    sub_branch_id = request.GET.get('sub_branch_id')

    if start_date and start_date not in ["", "None", None]:
        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            start_date = parse_datetime(start_date)
    else:
        start_date = None

    if end_date and end_date not in ["", "None", None]:
        try:
            end_date = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            end_date = parse_datetime(end_date)
            if end_date:
                end_date += timedelta(days=1)
    else:
        end_date = None

    # เริ่มสร้าง queryset
    cases = Case.objects.select_related('status','branch','category','sub_branch').all().order_by('-pk')

    if start_date and end_date:
        cases = cases.filter(date_created__gte=start_date, date_created__lt=end_date)

    if assign_name:
        cases = cases.filter(assign_name__username=assign_name)
    if status_id:
        cases = cases.filter(status_id=status_id)
    if branch_id:
        cases = cases.filter(branch_id=branch_id)
    if sub_branch_id:
        cases = cases.filter(sub_branch_id=sub_branch_id)

    # สำหรับผู้ใช้งานทั่วไปกรองตาม username
    if not request.user.is_staff:
        cases = cases.filter(create_username=create_username)
    # สำหรับ staff กรองตาม department_id
    elif request.user.is_staff:
        cases = cases.filter(department_id=department_id)

    # เขียน CSV
    for case in cases:
        date_created = case.date_created.strftime('%d/%m/%Y %H:%M') if case.date_created else ''
        receive_date = case.receive_date.strftime('%d/%m/%Y %H:%M') if case.receive_date else ''
        complete_date = case.complete_date.strftime('%d/%m/%Y %H:%M') if case.complete_date else ''

        writer.writerow([
            case.id,    
            case.category.name if case.category else '',
            case.sub_category.name if case.sub_category else '',
            case.second_sub_category.name if case.second_sub_category else '',
            case.subject_detail,
            case.case_detail,
            case.update_note,
            case.name, 
            date_created,
            receive_date,
            complete_date,
            case.assign_name.first_name + ' ' + case.assign_name.last_name if case.assign_name else '',
            case.branch.branch_name if case.branch else '',
            case.sub_branch.sub_branch_name if case.sub_branch else '', 
            case.status.name if case.status else '',
            case.score if case.score is not None else ''
        ])

    return response

def load_subbranches(request):
    branch_id = request.GET.get('branch_id')
    subbranches = SubBranch.objects.filter(branch_id=branch_id).values('sub_branch_id', 'sub_branch_name')
    return JsonResponse(list(subbranches), safe=False)