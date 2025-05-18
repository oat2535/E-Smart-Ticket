from django.urls import path
from .views import displayUser,register,addUser,deleteUser,editUser,updateUser,editPassword,updatePassword

urlpatterns = [
    path('displayUser',displayUser,name="displayUser"),
    path('addUser',addUser,name="addUser"),
    path('register/add',register,name="register"),
    path('register/delete/<int:id>',deleteUser,name="deleteUser"),
    path('register/edit/<int:id>',editUser,name="editUser"),
    path('register/update/<int:id>',updateUser,name="updateUser"),
    path('register/editpassword/<int:id>',editPassword,name="editPassword"),
    path('register/updatepassword/<int:id>',updatePassword,name="updatePassword")
]