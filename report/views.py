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
    cases = Case.objects.none()  # กำหนดค่าเริ่มต้นเป็น queryset ว่าง

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
    else:
        cases = Case.objects.none()

      # กรองตาม assign_name ถ้ามีการเลือก
    if assign_name:
        cases = cases.filter(assign_name=assign_name)
    
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
    status = Status.objects.all().order_by('pk')
    branches = Branch.objects.all().order_by('branch_name')
    sub_branches = SubBranch.objects.all().order_by('sub_branch_name')
    context = {
        'cases': cases,
        'start_date': start_date,
        'end_date': original_end_date,
        'create_username':create_username,
        'members': members,
        'assign_name': assign_name, 
        'status':status,
        'branches': branches,
        'sub_branches': sub_branches,
    }
    return render(request, "backend/report.html",context)

def export_csv(request):
    create_username = auth.get_user(request)
    department_id = request.user.department_id
    current_date = datetime.now().strftime('%Y-%m-%d')
     # กำหนดชื่อไฟล์
    filename = f'caseReport{current_date}.csv'
    # สร้าง HTTP Response พร้อม Header สำหรับดาวน์โหลด CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(u'\ufeff'.encode('utf-8-sig'))  # เขียน BOM สำหรับ Excel

    # เขียนข้อมูลใน CSV
    writer = csv.writer(response)
    writer.writerow(['รหัสเคส', 'ประเภท', 'รายละเอียด', 'ผู้แจ้งซ่อม', 'วันที่แจ้ง', 'วันที่รับเคส', 'วันที่ปิดเคส', 'Company', 'สาขา', 'สถานะ', 'คะแนน'])  # ใช้หัวข้อภาษาไทย

    # ดึงข้อมูลจากฐานข้อมูล
    if request.user.is_staff == 1:
        cases = Case.objects.select_related('status','branch','category','sub_branch').filter(department_id=department_id).order_by('-pk')
    else :
        cases = Case.objects.select_related('status','branch','category','sub_branch').filter(create_username=create_username).order_by('-pk')  # ใช้ select_related เพื่อดึงข้อมูล Status พร้อมกัน
  
    for case in cases:
        date_created = case.date_created.strftime('%d/%m/%Y %H:%M') if case.date_created else ''
        receive_date = case.receive_date.strftime('%d/%m/%Y %H:%M') if case.receive_date else ''
        complete_date = case.complete_date.strftime('%d/%m/%Y %H:%M') if case.complete_date else ''

        writer.writerow([
            case.id,    
            case.category.name, 
            case.case_detail,
            case.name, 
            date_created,
            receive_date,
            complete_date,
            case.branch.branch_name, 
            case.sub_branch.sub_branch_name, 
            case.status.name,
            case.score
        ])

    return response

def load_subbranches(request):
    branch_id = request.GET.get('branch_id')
    subbranches = SubBranch.objects.filter(branch_id=branch_id).values('sub_branch_id', 'sub_branch_name')
    return JsonResponse(list(subbranches), safe=False)