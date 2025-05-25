from django.shortcuts import render,redirect
from case.models import Case
from django.contrib.auth.decorators import login_required #import model บังคับต้องให้ login ก่อนเข้าใช้งาน
from django.contrib import auth,messages #import auth
from django.contrib.auth.models import User
from members.models import Members
from .forms import UserStaffStatusForm
from branch.models import Branch
from department.models import Department
from sub_branch.models import SubBranch
from django.http import JsonResponse


@login_required(login_url="member")
# Create your views here.
def displayUser(request):
    user = Members.objects.all().order_by('-pk').select_related('branch','sub_branch') #ดึงข้อมูลทั้งหมดจากฐานข้อมูล
    create_username = auth.get_user(request) #get user ตามที่ login

    return render(request,"backend/user.html",{
        "user":user,
        'create_username':create_username})

@login_required(login_url="member")
def addUser(request):
    user = Members.objects.all()
    create_username = request.user #get user ตามที่ login
    form = UserStaffStatusForm() 
    branches = Branch.objects.all()
    sub_branches = SubBranch.objects.all()
    departments = Department.objects.all()

    return render(request,"backend/addUser.html",{
        "user":user,
        'create_username':create_username,
        'form':form,'branches':branches,
        'departments':departments,'sub_branches':sub_branches})

@login_required(login_url="member")
def register(request):
    #เช็คข้อมูลรับค่าจาก form
    if request.method == "POST":
        user = Members.objects.all()
        form = UserStaffStatusForm(request.POST)
        branches = Branch.objects.all()
        sub_branches = SubBranch.objects.all()
        departments = Department.objects.all()
  
        username = request.POST["username"]
        first_name = request.POST["first_name"] 
        last_name = request.POST["last_name"]
        password = request.POST["password"] 
        repassword = request.POST["repassword"]
        branch = request.POST["branch"]
        sub_branches = request.POST["sub_branch"]
        phone_number = request.POST["phone_number"]
        department = request.POST.get("department", "").strip() 
        is_staff = request.POST.get("is_staff")  # รับค่าจากฟอร์ม

          # ตรวจสอบว่ากรอกข้อมูลครบ
        if not username or not first_name or not last_name or not password or not repassword:
            messages.info(request, "กรุณาป้อนข้อมูลให้ครบ!")
            return redirect("addUser")
        
        elif not branch:
            messages.info(request, "กรุณาเลือก Company !")
            return render(request,"backend/addUser.html", {
                "form": form,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "repassword": repassword,
                "phone_number": phone_number,
                "is_staff": is_staff,
                "branches": branches,
                "departments": departments,
                "selected_department": department  # เพิ่มข้อมูลแผนกที่เลือกไว้
            })
        elif not sub_branches:
            messages.info(request, "กรุณาเลือก Branch !")
            return render(request,"backend/addUser.html", {
                "form": form,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "repassword": repassword,
                "phone_number": phone_number,
                "is_staff": is_staff,
                "branches": branches,
                "departments": departments,
                "selected_department": department  # เพิ่มข้อมูลแผนกที่เลือกไว้
            })
        
        # elif not department:
        #     messages.info(request, "กรุณาเลือกแผนก !")
        #     return render(request,"backend/addUser.html", {
        #         "form": form,
        #         "username": username,
        #         "first_name": first_name,
        #         "last_name": last_name,
        #         "password": password,
        #         "repassword": repassword,
        #         "phone_number": phone_number,
        #         "is_staff": is_staff,
        #         "branches": branches,
        #         "selected_branch": branch,  # เพิ่มข้อมูลสาขาที่เลือกไว้
        #         "departments": departments,
        #     })
        
         # ตรวจสอบว่า username ซ้ำหรือไม่
        elif Members.objects.filter(username=username).exists():
            messages.info(request, f"ชื่อผู้ใช้ '{username}' มีผู้ใช้งานแล้ว!")
            return render(request,"backend/addUser.html", {
                "form": form,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "repassword": repassword,
                "phone_number": phone_number,
                "is_staff": is_staff,
                "branches": branches,
                "selected_branch": branch,
                "department": department
            })

        # ตรวจสอบรหัสผ่านว่าตรงกันหรือไม่
        elif password != repassword:
            messages.info(request, "รหัสผ่านไม่ตรงกัน!")
            return render(request,"backend/addUser.html", {
                "form": form,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "phone_number": phone_number,
                "is_staff": is_staff,
                "branches": branches,
                "selected_branch": branch,
                "department": department
            })

        else:
            if form.is_valid():
            # กำหนดค่า department_id เป็น None หากไม่ได้เลือก
                department_id = department if department else None
            # สร้างบัญชีผู้ใช้ใหม่
                is_staff_value = True if is_staff == 'on' else False
                user = Members.objects.create_user(
                        username = username,
                        first_name = first_name,
                        last_name = last_name,
                        branch_id = branch,
                        sub_branch_id = sub_branches,
                        phone_number = phone_number,
                        password = password,
                        department_id=department_id  # ใช้ค่า department_id
                    )
                user.is_staff = is_staff_value  # กำหนดค่า is_staff
                user.save()
                #messages.info(request, "สร้างบัญชีผู้ใช้สำเร็จ!")
                return redirect("displayUser")
    return redirect("displayUser")

@login_required(login_url="member")
def deleteUser(request,id):
    try:
        #ลบข้อมูลจากฐานข้อมูล
        user = Members.objects.get(id=id)
        user.delete() #ลบข้อมูล

        return redirect("displayUser")
    except:
        return redirect("displayUser")

@login_required(login_url="member")
def editUser(request,id):
    userEdit = Members.objects.get(id=id)
    create_username = auth.get_user(request) #get user ตามที่ login 
    form = UserStaffStatusForm(instance=userEdit) 
    branches = Branch.objects.all()
    sub_branches = SubBranch.objects.filter(branch_id=userEdit.branch_id)

    return render(request,"backend/editUser.html",{
        "userEdit":userEdit,
        'create_username':create_username,
        'form':form,'branches':branches,
        'sub_branches':sub_branches})

@login_required(login_url="member")
def updateUser(request,id):
    if request.method == "POST":
        #ดึงข้อมูลบทความที่ต้องการแก้ไขมาใช้งาน
        user = Members.objects.get(id=id)
        form = UserStaffStatusForm(request.POST, instance=user)

        #รับค่าจาก form
        username = request.POST["username"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        branch = request.POST["branch"]
        sub_branch = request.POST["sub_branch"]
        phone_number = request.POST["phone_number"]
        # permission = request.POST["permission"]

        if form.is_valid():
            #อัพเดทข้อมูล
            user.username = username
            user.first_name = first_name
            user.last_name = last_name 
            user.branch_id = branch
            user.sub_branch_id = sub_branch
            user.phone_number = phone_number
            # # กำหนดสิทธิ์ผู้ใช้ (is_staff) ตามค่า permission ที่ส่งมาจากฟอร์ม
            # if permission == "1":  # ถ้า checkbox ถูกติ๊ก (permission ส่งค่าเป็น '1')
            #     user.is_staff = True
            # else:  # ถ้า checkbox ไม่ถูกติ๊ก
            #     user.is_staff = False
            user.save()
            messages.info(request,"แก้ไขผู้ใช้เรียบร้อย")
            return redirect("editUser",id=id) #redirect กลับไปหน้า login
    return redirect("displayUser")

@login_required(login_url="member")
def editPassword(request,id):
    passwordEdit = Members.objects.get(id=id)
    create_username = auth.get_user(request) #get user ตามที่ login 

    # ตรวจสอบว่า user ที่ login เป็น staff หรือไม่
    if request.user.is_staff:  # ตรวจสอบว่าเป็น staff
        case = Case.objects.all()  # ถ้าเป็นแอดมิน ให้ดูทั้งหมด
        caseCountAll = case.count() #นับจำนวนบทความ
        caseCountPeding = Case.objects.filter(status_id=1).count()
        caseCountDoing = Case.objects.filter(status_id=2).count()
        caseCountDone = Case.objects.filter(status_id=3).count()
        caseCountCancel = Case.objects.filter(status_id=4).count()
        caseCountIT = Case.objects.filter(department_id="IT").count()
        caseCountPUR = Case.objects.filter(department_id="PUR").count()
        caseCountFIN = Case.objects.filter(department_id="FIN").count()
    else:
        case = Case.objects.filter(create_username=create_username).select_related('status','category','branch')  # แสดงกรณีที่เกี่ยวข้องกับ user นั้น
        caseCountAll = case.count() #นับจำนวนบทความ
        caseCountPeding = Case.objects.filter(status_id=1,create_username=create_username).count()
        caseCountDoing = Case.objects.filter(status_id=2,create_username=create_username).count()
        caseCountDone = Case.objects.filter(status_id=3,create_username=create_username).count()
        caseCountCancel = Case.objects.filter(status_id=4,create_username=create_username).count()
        caseCountIT = Case.objects.filter(department_id="IT",create_username=create_username).count()
        caseCountPUR = Case.objects.filter(department_id="PUR",create_username=create_username).count()
        caseCountFIN = Case.objects.filter(department_id="FIN",create_username=create_username).count()

    return render(request,"backend/editPassword.html",{
        "passwordEdit":passwordEdit,
        'create_username':create_username,
        'caseCountAll':caseCountAll,
        'caseCountPeding':caseCountPeding,
        'caseCountDoing':caseCountDoing,
        'caseCountDone':caseCountDone,
        'caseCountCancel':caseCountCancel,
        'caseCountIT':caseCountIT,
        'caseCountPUR':caseCountPUR,
        'caseCountFIN':caseCountFIN})

@login_required(login_url="member")
def updatePassword(request, id):
    if request.method == "POST":
        # ดึงข้อมูลผู้ใช้ที่ต้องการแก้ไข
        user = Members.objects.get(id=id)

        # รับค่าจากฟอร์ม
        password = request.POST["password"]
        repassword = request.POST["repassword"]

        if password == repassword:
            # เข้ารหัสรหัสผ่านและบันทึก
            user.set_password(password)
            user.save()

            messages.info(request, "แก้ไขรหัสผ่านเรียบร้อย")
            return redirect("editPassword", id=id)
        else:
            messages.info(request, "รหัสผ่านไม่ตรงกัน")
            return redirect("editPassword", id=id)

    return redirect("displayUser")


def load_subbranches(request):
    branch_id = request.GET.get('branch_id')
    subbranches = SubBranch.objects.filter(branch_id=branch_id).values('sub_branch_id', 'sub_branch_name')
    return JsonResponse(list(subbranches), safe=False)
