from django.urls import path
from . import views

app_name = 'assets_system'

urlpatterns = [
    path('', views.asset_list, name='asset_list'),
    path('<int:asset_id>/', views.asset_detail, name='asset_detail'),
    
    # Lists
    path('transfers/', views.transfer_list, name='transfer_list'),
    path('maintenances/', views.maintenance_list, name='maintenance_list'),
    path('writeoffs/', views.writeoff_list, name='writeoff_list'),
    path('disposals/', views.disposal_list, name='disposal_list'),
    
    # Workflow
    path('transfer/<int:asset_id>/', views.request_transfer, name='request_transfer'),
    path('writeoff/<int:asset_id>/', views.request_writeoff, name='request_writeoff'),
    path('disposal/<int:asset_id>/', views.request_disposal, name='request_disposal'),
    path('maintenance/<int:asset_id>/', views.request_maintenance, name='request_maintenance'),
    path('maintenance/approve/<int:maintenance_id>/<str:action>/', views.approve_maintenance, name='approve_maintenance'),
    path('writeoff/approve/<int:writeoff_id>/<str:action>/', views.approve_writeoff, name='approve_writeoff'),
    path('transfer/approve/<int:transfer_id>/<str:action>/', views.approve_transfer, name='approve_transfer'),
    path('disposal/approve/<int:disposal_id>/<str:action>/', views.approve_disposal, name='approve_disposal'),
    
    # QR Scan & Print
    path('scan/<int:asset_id>/', views.scan_qr, name='scan_qr'),
    path('print-qr/', views.print_qr_codes, name='print_qr_codes'),

    # AJAX
    path('ajax/load-sub-branches/', views.load_sub_branches, name='ajax_load_sub_branches'),
    path('ajax/fetch-ax-assets/', views.fetch_ax_assets, name='fetch_ax_assets'),
    path('ajax/sync-ax-assets/', views.sync_ax_assets, name='sync_ax_assets'),
    path('ajax/fetch-ax-updates/', views.fetch_ax_updates, name='fetch_ax_updates'),
    path('ajax/apply-ax-updates/', views.apply_ax_updates, name='apply_ax_updates'),
    path('ajax/sync-single-ax-asset/<int:asset_id>/', views.sync_single_ax_asset, name='sync_single_ax_asset'),
    path('ajax/add-sub-asset/<int:asset_id>/', views.ajax_add_sub_asset, name='ajax_add_sub_asset'),
    path('ajax/upload-asset-images/<int:asset_id>/', views.ajax_upload_asset_images, name='ajax_upload_asset_images'),
    path('ajax/delete-asset-images/', views.ajax_delete_additional_images, name='ajax_delete_additional_images'),
    path('ajax/search-assets/', views.search_assets_ajax, name='search_assets_ajax'),
]
