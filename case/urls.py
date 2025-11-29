from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import case,displayForm,insertData,deleteData,editData,updateData,addImages,uloadImages,deleteImage,load_subbranches,load_second_subcategories

urlpatterns = [
    path('',case,name="case"),
    path('displayForm',displayForm,name="displayForm"),
    # path('displayFormPUR',displayFormPUR,name="displayFormPUR"),
    path('insertData',insertData,name="insertData"),
    path('deleteData/<int:id>',deleteData,name="deleteData"),
    path('editData/<int:id>',editData,name="editData"),
    path('updateData/<int:id>',updateData,name="updateData"),
    path('addImages/<int:id>',addImages,name="addImages"),
    path('uloadImages/<int:id>',uloadImages,name="uloadImages"),
    path('deleteImage/<int:id>',deleteImage,name="deleteImage"),
    path('ajax/load-subbranches/', load_subbranches, name='ajax_load_subbranches'),
    path('ajax/load-second-subcategories/', load_second_subcategories, name='ajax_load_second_subcategories'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)