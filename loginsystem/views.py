from django.shortcuts import render,redirect
from django.contrib import messages,auth #import alert messages, auth
from django.contrib.auth.models import User #import model user (table user)

from django.views.decorators.csrf import ensure_csrf_cookie

# Create your views here.
@ensure_csrf_cookie
def index(request):
    return render(request,"backend/login.html")

def login(request):
    #รับค่าจาก form
    username = request.POST.get("username")
    password = request.POST.get("password")
    next_url = request.POST.get("next")

    #เก็บ session login
    user = auth.authenticate(username=username,password=password) # type: ignore

    if user is not None:
        auth.login(request,user) # type: ignore
        if next_url and next_url != 'None':
            return redirect(next_url)
        return redirect("case")
    else:
        from members.models import Members
        try:
            user_obj = Members.objects.get(username=username)
            if user_obj.check_password(password) and not user_obj.is_active:
                messages.info(request, "บัญชีผู้ใช้นี้ถูกระงับการใช้งาน (Inactive)")
            else:
                messages.info(request, "ไม่พบข้อมูลบัญชีผู้ใช้ หรือรหัสผ่านไม่ถูกต้อง")
        except Members.DoesNotExist:
            messages.info(request, "ไม่พบข้อมูลบัญชีผู้ใช้")

        if next_url and next_url != 'None':
            from django.urls import reverse
            return redirect(f"{reverse('member')}?next={next_url}")
        return redirect("member")

def logout(request):
    auth.logout(request) #สร้างฟังก์ชั่น logout
    return redirect("member")
