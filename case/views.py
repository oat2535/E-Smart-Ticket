from django.shortcuts import render,redirect
from case.models import Case
from django.contrib.auth.decorators import login_required #import model บังคับต้องให้ login ก่อนเข้าใช้งาน
from django.contrib import auth,messages #import auth
from category.models import Category
from sub_category.models import SubCategory
from second_sub_category.models import SecondSubCategory
from branch.models import Branch
from sub_branch.models import SubBranch
from status.models import Status
from django.core.files.storage import FileSystemStorage #import model อัพโหลด file
from members.models import Members
from department.models import Department
from priority.models import Priority
from case_image.models import CaseImage
from datetime import datetime
import os
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q, Max, OuterRef, Subquery
from datetime import datetime
from django.utils import timezone
from django.urls import reverse
from django.utils.dateparse import parse_date




# Create your views here.
@login_required(login_url="member")  # บังคับให้ login ก่อนใช้งาน
def case(request):
    user = request.user
    create_username = user.username  # ผู้ใช้งานที่ login
    branch = Members.objects.select_related('branch').all()
    priority = Priority.objects.all()
    members_qs = Members.objects.all()
    branches = Branch.objects.all().order_by('branch_name')
    status = Status.objects.all().order_by('pk')
    sub_categories = SubCategory.objects.all().order_by('name')

     # filter members ตาม department ของ user
    if user.username == "admin" or user.is_superuser:  # admin เห็นทุกคน
        members_qs = Members.objects.all().order_by("username")
    else:
        members_qs = Members.objects.filter(department_id=user.department_id).order_by("username")

     # กำหนดค่าเริ่มต้นให้กับตัวแปร
    caseCountPeding = 0
    caseCountDoing = 0
    caseCountDone = 0
    caseCountSatisfied = 0
    caseCountReceive = 0
    caseCountIT = 0
    caseCountPUR = 0
    caseCountFIN = 0
    caseCountITAssignName = 0

    if request.user.username == "admin" :  # ถ้าเป็นแอดมิน ให้ดูทั้งหมด
        case = Case.objects.all().order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
        caseCountPeding = Case.objects.filter(status_id=1).count()
        caseCountDoing = Case.objects.filter(status_id=2).count()
        caseCountDone = Case.objects.filter(status_id=5).count()
        caseCountSatisfied = Case.objects.filter(status_id=4).count()
        caseCountIT = Case.objects.filter(department_id="IT").count()
        caseCountPUR = Case.objects.filter(department_id="PUR").count()
        caseCountFIN = Case.objects.filter(department_id="FIN").count()
    elif user.department_id == "IT" and request.user.username == "kanchana":  # User kanchana ดูเฉพาะ IT ทั้งหมด
        case = Case.objects.filter(department_id="IT").order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority', 'assign_name')
        caseCountPeding = Case.objects.filter(status_id=1, department_id="IT").count()
        caseCountDoing = Case.objects.filter(status_id=2, department_id="IT").count()
        caseCountDone = Case.objects.filter(status_id=5, department_id="IT").count()
        caseCountSatisfied = Case.objects.filter(status_id=4, department_id="IT").count()
        caseCountIT = Case.objects.filter(department_id="IT").count()
        caseCountITAssignName = Case.objects.filter(department_id="IT", assign_name=user).count()
    elif user.department_id == "IT":  # User IT ดูเฉพาะเคสที่เกี่ยวข้องกับตัวเอง
        case = Case.objects.filter(department_id="IT").filter(Q(assign_name=user) | Q(assign_name__isnull=True)).order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority', 'assign_name')
        caseCountPeding = Case.objects.filter(status_id=1, department_id="IT").count()
        caseCountDoing = Case.objects.filter(status_id=2, department_id="IT", assign_name=user).count()
        caseCountDone = Case.objects.filter(status_id=5, department_id="IT", assign_name=user).count()
        caseCountSatisfied = Case.objects.filter(status_id=4, department_id="IT", assign_name=user).count()
        caseCountIT = Case.objects.filter(department_id="IT").count()
        caseCountITAssignName = Case.objects.filter(department_id="IT", assign_name=user).count()
    elif user.department_id == "PUR"  and request.user.username == "nisarat":  # User nisrat ดูเฉพาะ PUR ทั้งหมด
        case = Case.objects.filter(department_id="PUR").order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
        caseCountPeding = Case.objects.filter(status_id=1, department_id="PUR").count()
        caseCountDoing = Case.objects.filter(status_id=2, department_id="PUR").count()
        caseCountDone = Case.objects.filter(status_id=5, department_id="PUR").count()
        caseCountReceive = Case.objects.filter(status_id=7, department_id="PUR").count()
        caseCountPUR = Case.objects.filter(department_id="PUR").count()
    elif user.department_id == "PUR":  # User nisrat ดูเฉพาะ PUR ทั้งหมด
        case = Case.objects.filter(department_id="PUR").filter(Q(assign_name=user) | Q(assign_name__isnull=True)).order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
        caseCountPeding = Case.objects.filter(status_id=1, department_id="PUR", assign_name=user).count()
        caseCountDoing = Case.objects.filter(status_id=2, department_id="PUR", assign_name=user).count()
        caseCountDone = Case.objects.filter(status_id=5, department_id="PUR", assign_name=user).count()
        caseCountReceive = Case.objects.filter(status_id=7, department_id="PUR", assign_name=user).count()
        caseCountPUR = Case.objects.filter(department_id="PUR").count()
    # elif user.department_id == "FIN":  # ถ้าเป็นแอดมิน ให้ดูทั้งหมด
    #     case = Case.objects.filter(department_id="FIN").order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
    #     caseCountPeding = Case.objects.filter(status_id=1, department_id="FIN").count()
    #     caseCountDoing = Case.objects.filter(status_id=2, department_id="FIN").count()
    #     caseCountDone = Case.objects.filter(status_id=5, department_id="FIN").count()
    #     caseCountSatisfied = Case.objects.filter(status_id=4, department_id="FIN").count()
    #     caseCountFIN = Case.objects.filter(department_id="FIN").count()
    elif not request.user.is_staff:
        case = Case.objects.filter(create_username=create_username).order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
        caseCountPeding = Case.objects.filter(status_id=1, create_username=create_username).count()
        caseCountDoing = Case.objects.filter(status_id=2, create_username=create_username).count()
        caseCountDone = Case.objects.filter(status_id=5, create_username=create_username).count()
        caseCountSatisfied = Case.objects.filter(status_id=4, create_username=create_username).count()
        caseCountReceive = Case.objects.filter(status_id=7, department_id="PUR", create_username=create_username).count()
        caseCountIT = Case.objects.filter(department_id="IT", create_username=create_username).count()
        caseCountPUR = Case.objects.filter(department_id="PUR", create_username=create_username).count()
        caseCountFIN = Case.objects.filter(department_id="FIN", create_username=create_username).count()

    status_id = request.GET.get('status_id')
    department_id = request.GET.get('department_id')
    mycase = request.GET.get('mycase')
    request_date = request.GET.get('request_date')
    branch_id = request.GET.get('branch_id')
    
    if status_id:
        case = case.filter(status_id=status_id)

    if department_id:
        case = case.filter(department_id=department_id)

    if branch_id:
        case = case.filter(branch_id=branch_id)
    
    if mycase:
        case = case.filter(assign_name=mycase)
    
    if request_date:
        request_date = datetime.strptime(request_date, "%Y-%m-%d").date()
        case = case.filter(date_created__date=request_date)

    context = {
        'case': case,
        'caseCountFIN': caseCountFIN,
        'caseCountIT': caseCountIT,
        'caseCountPUR': caseCountPUR,
        'branch': branch,
        'create_username': create_username,
        'caseCountPeding': caseCountPeding,
        'caseCountDoing': caseCountDoing,
        'caseCountDone': caseCountDone,
        'caseCountSatisfied': caseCountSatisfied,
        'status_id': status_id,
        'priority': priority,
        'department_id': department_id,
        'caseCountReceive': caseCountReceive,
        'caseCountITAssignName': caseCountITAssignName,
        'mycase': mycase,
        'branches': branches,
        'status': status,
        'members_qs': members_qs,
        'sub_categories': sub_categories,
    }
    return render(request, "backend/index.html", context)

@login_required(login_url="member")
def displayForm(request):
    create_username = auth.get_user(request) #get user ตามที่ login
    department_id = request.GET.get('department_id')  # Get the department_id from the query parameter
    categories_it = Category.objects.filter(department_id="IT").order_by('pk')
    categories_pur = Category.objects.filter(department_id="PUR").order_by('pk')
    categories_fin = Category.objects.filter(department_id="FIN").order_by('pk')
    priorities = Priority.objects.all().order_by('pk')
    branches = Branch.objects.all()
    sub_branches = SubBranch.objects.all()

# Render ไฟล์ HTML ตาม department_id
    if department_id == 'IT':
        template = "backend/blogFormIT.html"
    elif department_id == 'PUR':
        template = "backend/blogFormPUR.html"
    elif department_id == 'FIN':
        template = "backend/blogFormFIN.html"
    else:
        return HttpResponse("Invalid department", status=400)

    return render(
        request,
        template,
        {
            'create_username': create_username,
            'priorities': priorities,
            'categories_it': categories_it,
            'categories_pur': categories_pur,
            'categories_fin': categories_fin,
            'branches': branches,
            'sub_branches': sub_branches,
            
        }
    )

@login_required(login_url="member")
def insertData(request):
    try:
        
        if request.method == "POST": #เช็คข้อมูลจากฟอร์มว่ามีข้อมูลในรูปแบบ file หรือไม่
            #รับค่าจากฟอร์ม
            dataFile = request.FILES.get("image", None)
            category = request.POST["category"]
            name = request.POST["name"]
            mobile = request.POST["mobile"]
            ip_address = request.POST["ip_address"]
            computer_name = request.POST["computer_name"]
            case_detail = request.POST["case_detail"]
            create_username = auth.get_user(request)
            # ✅ IT เลือก branch/sub_branch ได้เอง
            if request.user.department_id == "IT":
                branch = request.POST.get("branch")
                sub_branch = request.POST.get("sub_branch")
                sub_branch = sub_branch if sub_branch else None
            else:
                branch = request.user.branch_id
                sub_branch = request.user.sub_branch_id
            department = request.POST["department"]
            priority = request.POST["priority"]
            subject_detail = request.POST["subject_detail"]
            email = request.POST["email"]
           
            # ตรวจสอบว่าเป็นไฟล์หรือไม่
            source = request.POST.get('source', '')  # Get the source (where the form is coming from)

            # ถ้ามีการอัปโหลดไฟล์ ให้ทำการบันทึก
            img_url = None
            if dataFile:
                current_date = datetime.now().strftime("%Y%m%d%H%M%S")
                file_name, file_extension = os.path.splitext(dataFile.name)
                new_file_name = f"{file_name}_{current_date}{file_extension}"
                img_url = f"blogImages/{new_file_name}"

                fs = FileSystemStorage()
                fs.save(img_url, dataFile)

            # สร้าง Ticket Number
            today_str = datetime.now().strftime("%Y%m%d")
            prefix = f"{branch}-{today_str}"

            # ดึง Ticket ล่าสุดของวันนั้นจากสาขานั้น
            latest_ticket = Case.objects.filter(ticket_number__startswith=prefix).aggregate(Max("ticket_number"))["ticket_number__max"]

            if latest_ticket:
                last_number = int(latest_ticket.split("-")[-1])  # ดึงเลขท้าย
                new_number = last_number + 1
            else:
                new_number = 1

            ticket_number = f"{prefix}-{str(new_number).zfill(3)}"


            # บันทึกข้อมูล Case โดยไม่บังคับให้ต้องมีไฟล์
            status_id = 1
            case = Case(
                email=email, subject_detail=subject_detail, department_id=department,
                priority_id=priority, branch_id=branch, sub_branch_id=sub_branch, category_id=category, name=name,
                mobile=mobile, ip_address=ip_address, computer_name=computer_name,
                case_detail=case_detail, create_username=create_username,
                status_id=status_id, image=img_url if img_url else None, ticket_number=ticket_number,   # ถ้าไม่มีไฟล์ให้เป็น None
            )
            case.save()
            return JsonResponse({"status": "success", "message": "บันทึกข้อมูลเรียบร้อยแล้ว", "redirect_url": reverse("case") + f"?department_id={department}"})
    except Exception as e:
        messages.error(request, f"เกิดข้อผิดพลาด: {e}")  # แสดงข้อผิดพลาด
        return redirect("displayFormIT")

@login_required(login_url="member")
def deleteData(request,id):
    try:
        #ลบข้อมูลจากฐานข้อมูล
        case = Case.objects.get(id=id)
        # Delete the main image associated with the case
        fs = FileSystemStorage()
        if case.image:
            fs.delete(str(case.image))

        # Delete all associated case images
        case_images = CaseImage.objects.filter(case=case)
        for case_image in case_images:
            fs.delete(str(case_image.case_image))
            case_image.delete()

        # Delete the case object
        case.delete()
        return redirect("case")
    except:
        return redirect("case")

@login_required(login_url="member")
def editData(request,id):
    caseEdit = Case.objects.select_related('sub_category__category').get(id=id)
    caseImg = CaseImage.objects.filter(case_id=id)
    create_username = auth.get_user(request) #get user ตามที่ login 
    modify_username = auth.get_user(request).username
    categories_it = Category.objects.filter(department_id="IT").order_by('pk')
    categories_pur = Category.objects.filter(department_id="PUR") .order_by('pk')
    categories_fin = Category.objects.filter(department_id="FIN").order_by('pk')
     # ตรวจสอบไฟล์ PDF
    is_case_edit_pdf = caseEdit.image.name.endswith('.pdf') if caseEdit.image else False
    is_case_edit_excel = caseEdit.image.name.lower().endswith(('.xls', '.xlsx', '.csv')) if caseEdit.image else False
    for img in caseImg:
        # filename = img.case_image.name.lower() if img.case_image else ''
        img.is_pdf = img.case_image.name.endswith('.pdf')
        img.is_excel = img.case_image.name.endswith(('.xls', '.xlsx', '.csv'))
    categories = Category.objects.all()
    sub_categories = SubCategory.objects.filter(category=caseEdit.category).order_by('name')
    sub_category_names = sub_categories.values_list('name', flat=True)
    # ✅ ดึง SecondSubCategory ตาม SubCategory ของเคสปัจจุบัน
    second_sub_categories = SecondSubCategory.objects.filter(
        sub_category=caseEdit.sub_category
    ).order_by('name')
    second_sub_category_names = second_sub_categories.values_list('name', flat=True)
    branches = Branch.objects.all()
    sub_branches = SubBranch.objects.all()
    status = Status.objects.exclude(id__in=[4, 5, 7]).order_by('pk')
    status_user = Status.objects.exclude(id__in=[1, 2, 3, 4, 5, 7]).order_by('pk')
    assign_name = Members.objects.filter(is_staff=1).exclude(username="admin")
    assign_name_it = Members.objects.filter(is_staff=1, department_id="IT").exclude(username="admin")
    assigned_user = Members.objects.filter(username=caseEdit.assign_name).first()
    departments = Department.objects.all()
    priorities = Priority.objects.all()
    # ✅ ส่งค่าไปที่ template
    return render(request, "backend/editForm.html", {
        "caseImg": caseImg,
        "departments": departments,
        "priorities": priorities,
        "caseEdit": caseEdit,
        "create_username": create_username,
        "categories": categories,
        "categories_it": categories_it,
        "categories_pur": categories_pur,
        "categories_fin": categories_fin,
        "sub_categories": sub_categories,
        "sub_category_names": sub_category_names,
        "branches": branches,
        "status": status,
        "status_user": status_user,
        "assign_name": assign_name,
        "assign_name_it": assign_name_it,
        "assigned_user": assigned_user,
        "sub_branches": sub_branches,
        "modify_username": modify_username,
        "score_range": list(range(1, 11)),
        "is_case_edit_excel": is_case_edit_excel,
        "is_case_edit_pdf": is_case_edit_pdf,
        "second_sub_categories": second_sub_categories,
        "second_sub_category_names": second_sub_category_names,
    })
 

@login_required(login_url="member")
def updateData(request,id):
    try:
        if request.method == "POST":
            #ดึงข้อมูลบทความที่ต้องการแก้ไขมาใช้งาน
            case = Case.objects.get(id=id)

            #รับค่าจาก form
            branch = request.POST["branch"]
            category = request.POST["category"]
            sub_category = request.POST.get("sub_category")
            second_sub_category = request.POST.get("second_sub_category")
            priority = request.POST["priority"]
            name = request.POST["name"]
            mobile = request.POST["mobile"]
            ip_address = request.POST["ip_address"]
            computer_name = request.POST["computer_name"]
            subject_detail = request.POST["subject_detail"]
            case_detail = request.POST["case_detail"]
            email = request.POST["email"]
            status = int(request.POST.get("status_id"))
            update_note = request.POST.get("update_note", "")
            modify_username = auth.get_user(request).username
            score = request.POST.get("score",0)
            feedback = request.POST.get("feedback")
            product_receive_date = request.POST.get('product_receive_date')
            assign_name_input = request.POST.get("assign_name", "")  # จาก dropdown
            login_user = Members.objects.get(username=modify_username)  # user login

            if status in [4, 7]:
                if not score or int(score) == 0:
                    return JsonResponse({
                        "status": "warning",
                        "message": "กรุณาเลือกคะแนนความพึงพอใจ!"
                    })
                if status == 7 and not product_receive_date:
                    return JsonResponse({
                        "status": "warning",
                        "message": "กรุณาเลือกวันรับสินค้า!"
                    })               
            
            #อัพเดทข้อมูล
            case.branch_id = branch
            case.category_id = category
            # อัพเดท Category
            if category and str(case.category_id) != str(category):
                case.category_id = category  # เปลี่ยนเฉพาะเมื่อค่าต่างจากเดิม

            # อัพเดท Sub Category
            if sub_category:
                try:
                    sub_cat_obj = SubCategory.objects.get(id=int(sub_category))
                    if case.sub_category_id != sub_cat_obj.id:  # ตรวจว่าค่าต่างไหม
                        case.sub_category = sub_cat_obj
                except (SubCategory.DoesNotExist, ValueError):
                    pass
            else:
                # ถ้าผู้ใช้ลบค่าออกจาก select ให้ลบใน DB ด้วย
                if case.sub_category is not None:
                    case.sub_category = None

            # อัพเดท Second Sub Category
            if second_sub_category:
                try:
                    second_sub_cat_obj = SecondSubCategory.objects.get(id=int(second_sub_category))
                    if case.second_sub_category_id != second_sub_cat_obj.id:
                        case.second_sub_category = second_sub_cat_obj
                except (SecondSubCategory.DoesNotExist, ValueError):
                    pass
            else:
                if case.second_sub_category is not None:
                    case.second_sub_category = None

            case.priority_id = priority
            case.name = name
            case.mobile = mobile
            case.ip_address = ip_address
            case.computer_name = computer_name
            case.subject_detail = subject_detail
            case.email = email
            case.case_detail = case_detail
            case.modify_username = modify_username
            case.modify_date = timezone.now().replace(microsecond=0)

            # Logic สำหรับ assign_name และ status
            if case.status_id == 1 and status == 2:
                # อัพเดท receive_date เฉพาะกรณี receive_date ว่าง
                if case.receive_date == None:
                    case.receive_date = timezone.now().replace(microsecond=0)
                # kanchana สามารถเลือก assign_name จาก dropdown
                if request.user.username == "kanchana" and assign_name_input:
                    try:
                        member_it = Members.objects.get(username=assign_name_input)
                        case.assign_name = member_it
                    except Members.DoesNotExist:
                        pass
                # user อื่น และ assign_name ยังไม่เคยถูกเซ็ต
                elif not case.assign_name:
                    case.assign_name = login_user
                case.status_id = status

            elif case.status_id in [1, 2] and status == 3:
                # --- จากสถานะ 1 → 3 (Complete)
                if case.receive_date is None:
                    case.receive_date = timezone.now().replace(microsecond=0)
                case.complete_date = timezone.now().replace(microsecond=0)
                case.assign_name = login_user

                # ✅ ถ้าแผนกเป็น PUR ให้สถานะ = 7, ถ้าอื่น ๆ = 4
                if case.department_id == "PUR":
                    case.status_id = 7
                else:
                    case.status_id = 4

            elif status in [4, 7] and (score is not None or feedback):
                case.satisfied_date = timezone.now().replace(microsecond=0)
                case.status_id = 5
                case.satisfied_name = modify_username
                case.score = score
                case.feedback = feedback

            elif status in [1, 6]:
                case.cancel_date = timezone.now().replace(microsecond=0)
                case.cancel_name = modify_username
                case.status_id = status

            else:
                # กรณีอื่น ๆ เช่น status = 2 แต่ status_id เดิมไม่ใช่ 1 → ไม่อัพเดท assign_name
                case.status_id = status
            case.update_note = update_note
            case.save()
            return JsonResponse({
                "status": "success",
                "message": "บันทึกข้อมูลสำเร็จ",
                "redirect_url": reverse("case")
            })
     # ถ้าไม่ใช่ POST
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "status": "error",
                "message": "Invalid request method"
            }, status=400)
        else:
            return redirect("case")

    except Exception as e:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "status": "error",
                "message": str(e)
            }, status=500)
        else:
            messages.error(request, f"เกิดข้อผิดพลาด: {e}")
            return redirect("case")

@login_required(login_url="member")
def addImages(request,id):
    addImage = Case.objects.get(id=id)
    caseImage = CaseImage.objects.filter(case_id=id)
    create_username = auth.get_user(request) #get user ตามที่ login 
    for img in caseImage:
        img.is_pdf = img.case_image.name.endswith('.pdf') if img.case_image else False
        img.is_excel = img.case_image.name.endswith(('.xls', '.xlsx', '.csv'))
    return render(request,"backend/addImages.html",{
        "addImage":addImage,
        'create_username':create_username,
        'caseImage':caseImage})

@login_required(login_url="member")
def uloadImages(request, id):
    try:
        if request.method == "POST":
            dataFiles = request.FILES.getlist("case_image")

            if dataFiles:
                fs = FileSystemStorage()
                current_date = datetime.now().strftime("%Y%m%d%H%M%S")

                for file in dataFiles:
                    # ✅ ตั้งชื่อไฟล์ใหม่
                    file_name, file_extension = os.path.splitext(file.name)
                    new_file_name = f"{file_name}_{current_date}{file_extension}"
                    img_url = f"caseGallery/{new_file_name}"

                    # ✅ บันทึกไฟล์ลง storage
                    fs.save(img_url, file)

                    # ✅ บันทึกข้อมูลลงฐานข้อมูล
                    CaseImage.objects.create(case_id=id, case_image=img_url)
            return redirect("addImages", id=id)

    except Exception as e:
        messages.error(request, f"เกิดข้อผิดพลาด: {e}")
        return redirect("addImages", id=id)

@login_required(login_url="member")
def deleteImage(request, id):
    try:
        # ลบข้อมูลจากฐานข้อมูล
        case_image = CaseImage.objects.get(id=id)
        case_id = case_image.case_id

        # ลบภาพจากโฟลเดอร์
        fs = FileSystemStorage()
        fs.delete(str(case_image.case_image))

        # ลบข้อมูลรูปภาพ
        case_image.delete()

        return redirect("addImages", id=case_id)
    except Exception as e:
        messages.error(request, f"เกิดข้อผิดพลาด: {e}")
        return redirect("addImages", id=case_id)

# ✅ AJAX โหลด sub_branch ตาม company
def load_subbranches(request):
    branch_id = request.GET.get('branch_id')
    subbranches = SubBranch.objects.filter(branch_id=branch_id).values('sub_branch_id', 'sub_branch_name')
    return JsonResponse(list(subbranches), safe=False)

def load_second_subcategories(request):
    sub_category_id = request.GET.get('sub_category_id')
    second_subcategories = SecondSubCategory.objects.filter(sub_category_id=sub_category_id).values('id', 'name')
    return JsonResponse(list(second_subcategories), safe=False)

