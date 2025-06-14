from django.urls import path
from report.views import reportCase,export_csv,load_subbranches

urlpatterns = [
    path('reportCase',reportCase,name="reportCase"),
    path('export_csv/', export_csv, name='export_csv'),
    path('reportCase/ajax/load-subbranches/', load_subbranches, name='ajax_load_subbranches')
]