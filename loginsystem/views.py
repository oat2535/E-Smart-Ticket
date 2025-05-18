from django.shortcuts import render,redirect
from django.contrib import messages,auth #import alert messages, auth
from django.contrib.auth.models import User #import model user (table user)

# Create your views here.
def index(request):
    return render(request,"backend/login.html")

def login(request):
    #รับค่าจาก form
    username = request.POST["username"]
    password = request.POST["password"]

    #เก็บ session login
    user = auth.authenticate(username=username,password=password) # type: ignore

    if user is not None:
        auth.login(request,user) # type: ignore
        return redirect("case")
    else:
        messages.info(request,"ไม่พบข้อมูลบัญชีผู้ใช้")
        return redirect("member")

def logout(request):
    auth.logout(request) #สร้างฟังก์ชั่น logout
    return redirect("member")
