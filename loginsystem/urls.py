from django.urls import path
from .views import index,login,logout

urlpatterns = [
    path('member',index,name="member"),
    path('login',login,name="login"),
    path('logout',logout,name="logout")
]