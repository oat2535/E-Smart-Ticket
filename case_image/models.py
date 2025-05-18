from django.db import models
from case.models import Case

# Create your models here.
class CaseImage(models.Model):
    case_image = models.ImageField(upload_to="caseGallery",blank=True)
    case = models.ForeignKey(Case,on_delete=models.CASCADE,related_name="images")
    
    class Meta:
        db_table = "case_image"  # กำหนดชื่อ table ในฐานข้อมูล
        
    def __str__(self):
        return f"Image for Case: {self.case.name} (ID: {self.case.id})"