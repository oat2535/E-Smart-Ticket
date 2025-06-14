from django.shortcuts import render,redirect
from case.models import Case
from django.contrib.auth.decorators import login_required #import model บังคับต้องให้ login ก่อนเข้าใช้งาน
from django.contrib import auth,messages #import auth
from category.models import Category
from sub_category.models import SubCategory
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
from django.http import HttpResponse
from django.db.models import Count, Q, Max
from datetime import datetime
from django.utils import timezone
from django.urls import reverse



# Create your views here.
@login_required(login_url="member")  # บังคับให้ login ก่อนใช้งาน
def case(request):
    user = request.user
    create_username = user.username  # ผู้ใช้งานที่ login
    branch = Members.objects.select_related('branch').all()
    priority = Priority.objects.all()
     # กำหนดค่าเริ่มต้นให้กับตัวแปร
    caseCountPeding = 0
    caseCountDoing = 0
    caseCountDone = 0
    caseCountSatisfied = 0
    caseCountReceive = 0
    caseCountIT = 0
    caseCountPUR = 0
    caseCountFIN = 0

    if request.user.username == "admin":  # ถ้าเป็นแอดมิน ให้ดูทั้งหมด
        case = Case.objects.all().order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
        caseCountPeding = Case.objects.filter(status_id=1).count()
        caseCountDoing = Case.objects.filter(status_id=2).count()
        caseCountDone = Case.objects.filter(status_id=5).count()
        caseCountSatisfied = Case.objects.filter(status_id=4).count()
        caseCountIT = Case.objects.filter(department_id="IT").count()
        caseCountPUR = Case.objects.filter(department_id="PUR").count()
        caseCountFIN = Case.objects.filter(department_id="FIN").count()
    elif user.department_id == "IT":  # ถ้าเป็นแอดมิน ให้ดูทั้งหมด
        case = Case.objects.filter(department_id="IT").order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
        caseCountPeding = Case.objects.filter(status_id=1, department_id="IT").count()
        caseCountDoing = Case.objects.filter(status_id=2, department_id="IT").count()
        caseCountDone = Case.objects.filter(status_id=5, department_id="IT").count()
        caseCountSatisfied = Case.objects.filter(status_id=4, department_id="IT").count()
        caseCountIT = Case.objects.filter(department_id="IT").count()
    elif user.department_id == "PUR":  # ถ้าเป็นแอดมิน ให้ดูทั้งหมด
        case = Case.objects.filter(department_id="PUR").order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
        caseCountPeding = Case.objects.filter(status_id=1, department_id="PUR").count()
        caseCountDoing = Case.objects.filter(status_id=2, department_id="PUR").count()
        caseCountDone = Case.objects.filter(status_id=5, department_id="PUR").count()
        caseCountReceive = Case.objects.filter(status_id=7, department_id="PUR").count()
        caseCountPUR = Case.objects.filter(department_id="PUR").count()
    elif user.department_id == "FIN":  # ถ้าเป็นแอดมิน ให้ดูทั้งหมด
        case = Case.objects.filter(department_id="FIN").order_by('-pk').select_related('status', 'category', 'branch', 'department', 'priority')
        caseCountPeding = Case.objects.filter(status_id=1, department_id="FIN").count()
        caseCountDoing = Case.objects.filter(status_id=2, department_id="FIN").count()
        caseCountDone = Case.objects.filter(status_id=5, department_id="FIN").count()
        caseCountSatisfied = Case.objects.filter(status_id=4, department_id="FIN").count()
        caseCountFIN = Case.objects.filter(department_id="FIN").count()
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

    if status_id:
        case = case.filter(status_id=status_id)

    if department_id:
        case = case.filter(department_id=department_id)

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
            
        }
    )

@login_required(login_url="member")
def insertData(request):
    try:
        
        if request.method == "POST": #เช็คข้อมูลจากฟอร์มว่ามีข้อมูลในรูปแบบ file หรือไม่
            categories_it = Category.objects.filter(department_id="IT").order_by('pk')
            categories_pur = Category.objects.filter(department_id="PUR") .order_by('pk')
            categories_fin = Category.objects.filter(department_id="FIN").order_by('pk')
            priorities = Priority.objects.all().order_by('pk')

            #รับค่าจากฟอร์ม
            dataFile = request.FILES.get("image", None)
            category = request.POST["category"]
            name = request.POST["name"]
            mobile = request.POST["mobile"]
            ip_address = request.POST["ip_address"]
            computer_name = request.POST["computer_name"]
            case_detail = request.POST["case_detail"]
            create_username = auth.get_user(request)
            branch = request.user.branch_id
            sub_branch = request.user.sub_branch_id
            department = request.POST["department"]
            priority = request.POST["priority"]
            subject_detail = request.POST["subject_detail"]
            email = request.POST["email"]
           
            # ตรวจสอบว่าเป็นไฟล์หรือไม่
            source = request.POST.get('source', '')  # Get the source (where the form is coming from)

            if not category:
                messages.error(request, "กรุณาเลือก ประเภท!")
                if source == "blogFormPUR":
                    return render(request, "backend/blogFormPUR.html", {
                        "name": name,
                        "mobile": mobile,
                        "ip_address": ip_address,
                        "computer_name": computer_name,
                        "case_detail": case_detail,
                        "subject_detail": subject_detail,
                        "categories_pur": categories_pur,
                        "selected_category": category,
                        "selected_priority": priority,
                        "priorities": priorities,
                        "department": department,
                        "email": email,
                        "create_username": create_username
                    })
                elif source == "blogFormFIN":
                    return render(request, "backend/blogFormFIN.html", {
                        "name": name,
                        "mobile": mobile,
                        "ip_address": ip_address,
                        "computer_name": computer_name,
                        "case_detail": case_detail,
                        "subject_detail": subject_detail,
                        "categories_fin": categories_fin,
                        "selected_category": category,
                        "selected_priority": priority,
                        "priorities": priorities,
                        "department": department,
                        "email": email,
                        "create_username": create_username
                    })
                return render(request, "backend/blogFormIT.html", {
                    "name": name,
                    "mobile": mobile,
                    "ip_address": ip_address,
                    "computer_name": computer_name,
                    "case_detail": case_detail,
                    "subject_detail": subject_detail,
                    "categories_it": categories_it,
                    "selected_category": category,
                    "selected_priority": priority,
                    "priorities": priorities,
                    "department": department,
                    "email": email,
                    "create_username": create_username
                })

            if not priority:
                messages.error(request, "กรุณาเลือก ระดับความสำคัญ!")
                if source == "blogFormPUR":
                    return render(request, "backend/blogFormPUR.html", {
                        "name": name,
                        "mobile": mobile,
                        "ip_address": ip_address,
                        "computer_name": computer_name,
                        "case_detail": case_detail,
                        "subject_detail": subject_detail,
                        "categories_pur": categories_pur,
                        "selected_category": category,
                        "selected_priority": priority,
                        "priorities": priorities,
                        "department": department,
                        "email": email,
                        "create_username": create_username
                    })
                elif source == "blogFormFIN":
                    return render(request, "backend/blogFormFIN.html", {
                        "name": name,
                        "mobile": mobile,
                        "ip_address": ip_address,
                        "computer_name": computer_name,
                        "case_detail": case_detail,
                        "subject_detail": subject_detail,
                        "categories_fin": categories_fin,
                        "selected_category": category,
                        "selected_priority": priority,
                        "priorities": priorities,
                        "department": department,
                        "email": email,
                        "create_username": create_username
                    })
                return render(request, "backend/blogFormIT.html", {
                    "name": name,
                    "mobile": mobile,
                    "ip_address": ip_address,
                    "computer_name": computer_name,
                    "case_detail": case_detail,
                    "subject_detail": subject_detail,
                    "categories_it": categories_it,
                    "selected_category": category,
                    "selected_priority": priority,
                    "priorities": priorities,
                    "department": department,
                    "email": email,
                    "create_username": create_username
                })

            # บังคับให้แนบไฟล์หรือรูปภาพ
            # elif not dataFile:
            #     messages.error(request, "กรุณาอัปโหลดรูปภาพ!")
            #     if source == "blogFormPUR":
            #         return render(request, "backend/blogFormPUR.html", {
            #             "name": name,
            #             "mobile": mobile,
            #             "ip_address": ip_address,
            #             "computer_name": computer_name,
            #             "case_detail": case_detail,
            #             "subject_detail": subject_detail,
            #             "categories_pur": categories_pur,
            #             "selected_category": category,
            #             "selected_priority": priority,
            #             "priorities": priorities,
            #             "department": department,
            #             "email": email,
            #             "create_username": create_username
            #         }) 
            #     elif source == "blogFormFIN":
            #         return render(request, "backend/blogFormFIN.html", {
            #             "name": name,
            #             "mobile": mobile,
            #             "ip_address": ip_address,
            #             "computer_name": computer_name,
            #             "case_detail": case_detail,
            #             "subject_detail": subject_detail,
            #             "categories_fin": categories_fin,
            #             "selected_category": category,
            #             "selected_priority": priority,
            #             "priorities": priorities,
            #             "department": department,
            #             "email": email,
            #             "create_username": create_username
            #         })
            #     return render(request, "backend/blogFormIT.html", {
            #         "name": name,
            #         "mobile": mobile,
            #         "ip_address": ip_address,
            #         "computer_name": computer_name,
            #         "case_detail": case_detail,
            #         "subject_detail": subject_detail,
            #         "categories_it": categories_it,
            #         "selected_category": category,
            #         "selected_priority": priority,
            #         "priorities": priorities,
            #         "department": department,
            #         "email": email,
            #         "create_username": create_username
            #     })  
              
            # รายการของ mimetypes ที่อนุญาต
            ALLOWED_CONTENT_TYPES = [
                "image/jpeg", "image/png", "application/pdf",
                "application/vnd.ms-excel",  # .xls
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
                "text/csv", "application/csv", "application/vnd.ms-excel"  # .csv (บาง browser อาจใช้แบบนี้)
            ]

            # ขนาดไฟล์สูงสุด (10MB)
            MAX_FILE_SIZE = 10 * 1024 * 1024  # bytes

            if dataFile:  # ตรวจสอบว่าอัปโหลดไฟล์มาหรือไม่
                if dataFile.content_type not in ALLOWED_CONTENT_TYPES:
                    messages.error(request, "ไฟล์ที่อัปโหลดไม่รองรับ กรุณาอัปโหลดไฟล์รูปภาพหรือ PDF เท่านั้น!")
                if dataFile.size > MAX_FILE_SIZE:
                    messages.error(request, "ขนาดไฟล์เกิน 10MB กรุณาอัปโหลดไฟล์ที่มีขนาดไม่เกิน 10MB!")
                    if source == "blogFormPUR":
                        return render(request, "backend/blogFormPUR.html", {
                            "name": name,
                            "mobile": mobile,
                            "ip_address": ip_address,
                            "computer_name": computer_name,
                            "case_detail": case_detail,
                            "subject_detail": subject_detail,
                            "categories_pur": categories_pur,
                            "selected_category": category,
                            "selected_priority": priority,
                            "priorities": priorities,
                            "department": department,
                            "email": email,
                            "create_username": create_username
                        }) 
                    elif source == "blogFormFIN":
                        return render(request, "backend/blogFormFIN.html", {
                            "name": name,
                            "mobile": mobile,
                            "ip_address": ip_address,
                            "computer_name": computer_name,
                            "case_detail": case_detail,
                            "subject_detail": subject_detail,
                            "categories_fin": categories_fin,
                            "selected_category": category,
                            "selected_priority": priority,
                            "priorities": priorities,
                            "department": department,
                            "email": email,
                            "create_username": create_username
                        }) 
                    return render(request, "backend/blogFormIT.html", {
                        "name": name,
                        "mobile": mobile,
                        "ip_address": ip_address,
                        "computer_name": computer_name,
                        "case_detail": case_detail,
                        "subject_detail": subject_detail,
                        "categories_it": categories_it,
                        "selected_category": category,
                        "selected_priority": priority,
                        "priorities": priorities,
                        "department": department,
                        "email": email,
                        "create_username": create_username
                    })


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
            if source == "blogFormIT":
                return redirect(reverse("case") + "?department_id=IT")
            if source == "blogFormPUR":
                return redirect(reverse("case") + "?department_id=PUR")
            if source == "blogFormFIN":
                return redirect(reverse("case") + "?department_id=FIN")
            #return redirect("case")
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
    sub_categories = SubCategory.objects.all()
    sub_categories_1 = SubCategory.objects.filter(category_id=1)
    sub_categories_2 = SubCategory.objects.filter(category_id=2)
    sub_categories_3 = SubCategory.objects.filter(category_id=3)
    branches = Branch.objects.all()
    sub_branches = SubBranch.objects.all()
    status = Status.objects.exclude(id__in=[4, 5, 7]).order_by('pk')
    status_user = Status.objects.exclude(id__in=[1, 2, 3, 4, 5, 7]).order_by('pk')
    assign_name = Members.objects.filter(is_staff=1).exclude(username="admin")
    assigned_user = Members.objects.filter(username=caseEdit.assign_name).first()
    departments = Department.objects.all()
    priorities = Priority.objects.all()
    return render(request,"backend/editForm.html",{
        "caseImg":caseImg,
        "departments":departments,
        "priorities":priorities,
        "caseEdit":caseEdit,
        'create_username':create_username,
        'categories':categories,
        'categories_it':categories_it,
        'categories_pur':categories_pur,
        'categories_fin':categories_fin,
        'sub_categories':sub_categories,
        'sub_categories_1':sub_categories_1,
        'sub_categories_2':sub_categories_2,
        'sub_categories_3':sub_categories_3,
        'branches':branches,
        'status':status,
        'status_user':status_user,
        'assign_name':assign_name,
        'assigned_user':assigned_user,
        'sub_branches':sub_branches,
        'modify_username':modify_username,
        'score_range' : list(range(1, 11)),
        'is_case_edit_excel': is_case_edit_excel,
        "is_case_edit_pdf": is_case_edit_pdf})

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
            priority = request.POST["priority"]
            name = request.POST["name"]
            mobile = request.POST["mobile"]
            ip_address = request.POST["ip_address"]
            computer_name = request.POST["computer_name"]
            subject_detail = request.POST["subject_detail"]
            case_detail = request.POST["case_detail"]
            email = request.POST["email"]
            status = int(request.POST.get("status_id"))
            assign_name = auth.get_user(request).username
            update_note = request.POST.get("update_note", "")
            modify_username = auth.get_user(request).username
            score = request.POST.get("score",0)
            feedback = request.POST.get("feedback")
            product_receive_date = request.POST.get('product_receive_date')

            if status in [4,7] and int(score) == 0 and request.user.is_staff == 0 :
                messages.error(request, "กรุณาเลือกคะแนนความพึงพอใจ !")
                caseEdit = Case.objects.select_related('sub_category__category').get(id=id)
                caseImg = CaseImage.objects.filter(case_id=id)
                assign_name = Members.objects.filter(is_staff=1).exclude(username="admin")
                assigned_user = Members.objects.filter(username=caseEdit.assign_name).first()

                for img in caseImg:
                    img.is_pdf = img.case_image.name.endswith('.pdf')
                    img.is_excel = img.case_image.name.endswith(('.xls', '.xlsx', '.csv'))

                categories_it = Category.objects.filter(department_id="IT").order_by('pk')
                categories_pur = Category.objects.filter(department_id="PUR").order_by('pk')
                categories_fin = Category.objects.filter(department_id="FIN").order_by('pk')

                return render(request, "backend/editForm.html", {
                    "caseImg": caseImg,
                    "departments": Department.objects.all(),
                    "priorities": Priority.objects.all(),
                    "caseEdit": caseEdit,
                    'create_username': auth.get_user(request),
                    'categories': Category.objects.all(),
                    'categories_it': categories_it,
                    'categories_pur': categories_pur,
                    'categories_fin': categories_fin,
                    'sub_categories': SubCategory.objects.all(),
                    'sub_categories_1': SubCategory.objects.filter(category_id=1),
                    'sub_categories_2': SubCategory.objects.filter(category_id=2),
                    'sub_categories_3': SubCategory.objects.filter(category_id=3),
                    'branches': Branch.objects.all(),
                    'status': Status.objects.exclude(id__in=[4, 5, 7]).order_by('pk'),
                    'status_user': Status.objects.exclude(id__in=[1, 2, 3, 4, 5, 7]).order_by('pk'),
                    'assign_name': assign_name,
                    'assigned_user': assigned_user,
                    'sub_branches': SubBranch.objects.all(),
                    'modify_username': auth.get_user(request).username,
                    'feedback': feedback,
                    "score_range": list(range(1, 11)),
                    'product_receive_date': product_receive_date,
                    'is_case_edit_excel': caseEdit.image.name.lower().endswith(('.xls', '.xlsx', '.csv')) if caseEdit.image else False,
                    "is_case_edit_pdf": caseEdit.image.name.endswith('.pdf') if caseEdit.image else False
                })
            
            if status == 7 and not product_receive_date and request.user.is_staff == 0:
                messages.error(request, "กรุณาเลือกวันรับสินค้า !")
                caseEdit = Case.objects.select_related('sub_category__category').get(id=id)
                caseImg = CaseImage.objects.filter(case_id=id)
                assign_name = Members.objects.filter(is_staff=1).exclude(username="admin")
                assigned_user = Members.objects.filter(username=caseEdit.assign_name).first()

                for img in caseImg:
                    img.is_pdf = img.case_image.name.endswith('.pdf')
                    img.is_excel = img.case_image.name.endswith(('.xls', '.xlsx', '.csv'))

                categories_it = Category.objects.filter(department_id="IT").order_by('pk')
                categories_pur = Category.objects.filter(department_id="PUR").order_by('pk')
                categories_fin = Category.objects.filter(department_id="FIN").order_by('pk')

                return render(request, "backend/editForm.html", {
                    "caseImg": caseImg,
                    "departments": Department.objects.all(),
                    "priorities": Priority.objects.all(),
                    "caseEdit": caseEdit,
                    'create_username': auth.get_user(request),
                    'categories': Category.objects.all(),
                    'categories_it': categories_it,
                    'categories_pur': categories_pur,
                    'categories_fin': categories_fin,
                    'sub_categories': SubCategory.objects.all(),
                    'sub_categories_1': SubCategory.objects.filter(category_id=1),
                    'sub_categories_2': SubCategory.objects.filter(category_id=2),
                    'sub_categories_3': SubCategory.objects.filter(category_id=3),
                    'branches': Branch.objects.all(),
                    'status': Status.objects.exclude(id__in=[4, 5, 7]).order_by('pk'),
                    'status_user': Status.objects.exclude(id__in=[1, 2, 3, 4, 5, 7]).order_by('pk'),
                    'assign_name': assign_name,
                    'assigned_user': assigned_user,
                    'sub_branches': SubBranch.objects.all(),
                    'modify_username': auth.get_user(request).username,
                    'feedback': feedback,
                    "score_range": list(range(1, 11)),
                    'score': score,
                    'product_receive_date': product_receive_date,
                    'is_case_edit_excel': caseEdit.image.name.lower().endswith(('.xls', '.xlsx', '.csv')) if caseEdit.image else False,
                    "is_case_edit_pdf": caseEdit.image.name.endswith('.pdf') if caseEdit.image else False
                })

                                
            #อัพเดทข้อมูล
            case.branch_id = branch
            case.category_id = category
            if not sub_category:  # กรณีไม่ได้เลือกค่า
                case.sub_category = None
            else:
                try:
                    case.sub_category = SubCategory.objects.get(id=int(sub_category))
                except (SubCategory.DoesNotExist, ValueError):
                    case.sub_category = None  # fallback กัน error กรณี id ไม่ถูกต้อง
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

            if case.status_id == 1 and status == 3:
                case.receive_date = timezone.now().replace(microsecond=0)
                case.complete_date = timezone.now().replace(microsecond=0)
                case.assign_name = assign_name
                         
            if status in [1,6]:  
                case.cancel_date = timezone.now().replace(microsecond=0)
                case.cancel_name = modify_username
                case.status_id = status       

            if status == 3 and case.department_id == "PUR":
                case.complete_date = timezone.now().replace(microsecond=0)
                case.status_id = 7
                case.assign_name = modify_username
            elif status == 3:
                case.complete_date = timezone.now().replace(microsecond=0)
                case.status_id = 4
                case.assign_name = modify_username
            elif status == 2:
                case.receive_date = timezone.now().replace(microsecond=0)
                case.assign_name = assign_name
                case.status_id = status
            elif status == 4 and (score is not None or feedback):
                case.satisfied_date = timezone.now().replace(microsecond=0)
                case.status_id = 5
                case.satisfied_name = modify_username
                case.score = score
                case.feedback = feedback
            elif status == 7 and (score is not None or feedback):
                case.satisfied_date = timezone.now().replace(microsecond=0)
                if product_receive_date:
                    try:
                        product_receive_date_dt = datetime.strptime(product_receive_date, "%d %b %Y, %I:%M %p")
                        case.product_receive_date = product_receive_date_dt
                    except ValueError:
                        messages.error(request, "กรุณาเลือกวันที่รับสินค้า")
                        return redirect("editData", id=id)
                case.status_id = 5
                case.satisfied_name = modify_username
                case.score = score
                case.feedback = feedback
            elif status == 6:
                case.cancel_date = timezone.now().replace(microsecond=0)
                case.cancel_name = modify_username
                case.status_id = status
            else:
                case.status_id = status
            case.update_note = update_note
            case.save()

        # #อัพเดทภาพปก
        # if "image" in request.FILES:
        #     dataFile = request.FILES["image"]
        #     if str(dataFile.content_type).startswith("image"):
        #         #ลบภาพเก่าในโฟลเดอร์ออก
        #         fs = FileSystemStorage()
        #         if case.image:  # ตรวจสอบว่ามีภาพเก่าอยู่หรือไม่
        #             fs.delete(str(case.image))
                
        #         #แทนที่ภาพใหม่
        #         img_url = "caseImages/"+dataFile.name
        #         filename = fs.save(img_url,dataFile)
        #         case.image = img_url
        #         case.save()
        # messages.info(request,"อัพเดทข้อมูลสำเร็จ")
        return redirect("case")
    except Exception as e:
        messages.error(request, f"เกิดข้อผิดพลาด: {e}")  # แสดงข้อผิดพลาด
        return redirect("case")

@login_required(login_url="member")
def addImages(request,id):
    addImage = Case.objects.get(id=id)
    caseImage = CaseImage.objects.filter(case_id=id)
    create_username = auth.get_user(request) #get user ตามที่ login 
    for img in caseImage:
        # filename = img.case_image.name.lower() if img.case_image else ''
        img.is_pdf = img.case_image.name.endswith('.pdf') if img.case_image else False
        img.is_excel = img.case_image.name.endswith(('.xls', '.xlsx', '.csv'))
    # # ตรวจสอบไฟล์ PDF
    # is_case_edit_pdf = caseEdit.image.name.endswith('.pdf') if caseEdit.image else False
    # is_case_edit_excel = caseEdit.image.name.lower().endswith(('.xls', '.xlsx', '.csv')) if caseEdit.image else False
    # for img in caseImg:
    #     # filename = img.case_image.name.lower() if img.case_image else ''
    #     img.is_pdf = img.case_image.name.endswith('.pdf')
    #     img.is_excel = img.case_image.name.endswith(('.xls', '.xlsx', '.csv'))


    return render(request,"backend/addImages.html",{
        "addImage":addImage,
        'create_username':create_username,
        'caseImage':caseImage})

@login_required(login_url="member")
def uloadImages(request, id):
    try:
        if request.method == "POST":
            dataFiles = request.FILES.getlist("case_image")


             # ประเภทไฟล์ที่อนุญาต
            ALLOWED_CONTENT_TYPES = [
                "image/jpeg", "image/png", "application/pdf",
                "application/vnd.ms-excel",  # .xls
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
                "text/csv", "application/csv"
            ]

            # ขนาดไฟล์สูงสุด (10MB)
            MAX_FILE_SIZE = 10 * 1024 * 1024  # bytes

            for dataFile in dataFiles:
                # ✅ ตรวจสอบประเภทไฟล์ (แก้ logic ตรงนี้)
                if dataFile.content_type not in ALLOWED_CONTENT_TYPES:
                    messages.error(request, "ประเภทไฟล์ไม่ถูกต้อง! กรุณาอัปโหลดเฉพาะไฟล์รูปภาพ, PDF, Excel หรือ CSV เท่านั้น")
                    return redirect("addImages", id=id)

                # ✅ ตรวจสอบขนาดไฟล์
                if dataFile.size > MAX_FILE_SIZE:
                    messages.error(request, "ขนาดไฟล์เกิน 10MB กรุณาอัปโหลดไฟล์ที่มีขนาดไม่เกิน 10MB!")
                    return redirect("addImages", id=id)

                # ✅ ตั้งชื่อไฟล์ใหม่
                current_date = datetime.now().strftime("%Y%m%d%H%M%S")
                file_name, file_extension = os.path.splitext(dataFile.name)
                new_file_name = f"{file_name}_{current_date}{file_extension}"
                img_url = f"caseGallery/{new_file_name}"

                # ✅ บันทึกไฟล์ลง storage
                fs = FileSystemStorage()
                fs.save(img_url, dataFile)

                # ✅ บันทึกข้อมูลลงฐานข้อมูล
                CaseImage.objects.create(case_id=id, case_image=img_url)

            messages.success(request, "อัปโหลดไฟล์สำเร็จ")
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

