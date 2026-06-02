from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='access_dashboard'),
    path('requests/', views.request_list, name='access_request_list'),
    path('requests/new/', views.create_request, name='access_create_request'),
    path('requests/<int:pk>/', views.request_detail, name='access_request_detail'),
    path('approvals/', views.approval_list, name='access_approval_list'),
    path('approvals/<int:pk>/approve/', views.approve_request, name='access_approve_request'),
    path('approvals/<int:pk>/reject/', views.reject_request, name='access_reject_request'),
    path('request-access/', views.public_create_request, name='access_public_create_request'),
]
