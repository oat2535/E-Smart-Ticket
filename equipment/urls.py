from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/add/', views.add_equipment, name='add_equipment'),
    path('equipment/edit/<int:equipment_id>/', views.edit_equipment, name='edit_equipment'),
    path('equipment/delete/<int:equipment_id>/', views.delete_equipment, name='delete_equipment'),
    path('search-equipment/', views.search_equipment, name='search_equipment'),
    # path('add-to-cart/<int:equipment_id>/', views.add_to_cart, name='add_to_cart'),
    # path('cart/', views.cart_detail, name='cart_detail'),
    # path('cart/remove/<int:equipment_id>/', views.remove_from_cart, name='remove_from_cart'),
    # path('cart/clear/', views.clear_cart, name='clear_cart'),
    # path('checkout/', views.checkout, name='checkout'),
    path('request/<int:equipment_id>/', views.equipment_request, name='equipment_request'),
    path('my-requests/', views.my_requests, name='my_requests'),
    path('manage-requests/', views.manage_requests, name='manage_requests'),
    path('manage-requests/approve/<int:requisition_id>/', views.approve_request, name='approve_request'),
    path('manage-requests/reject/<int:requisition_id>/', views.reject_request, name='reject_request'),
    path('manage-requests/receive/<int:requisition_id>/', views.receive_request, name='receive_request'),
    path('manage-requests/receive/<int:requisition_id>/', views.receive_request, name='receive_request'),
    path('report/', views.request_report, name='request_report'),
    path('scan/', views.scan_qr, name='scan_qr'),
]
