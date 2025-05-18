from django.urls import path
from report.views import reportCase,export_csv

urlpatterns = [
    path('reportCase',reportCase,name="reportCase"),
    path('export_csv/', export_csv, name='export_csv')
]