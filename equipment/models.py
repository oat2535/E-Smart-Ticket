from django.db import models
from django.db.models import Sum
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Equipment(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    total_quantity = models.PositiveIntegerField(default=0)
    available_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True)
    description = models.TextField(blank=True)
    serial_number = models.CharField(max_length=100, unique=True, blank=True, null=True)

    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('MAINTENANCE', 'Maintenance'),
        ('LOST', 'Lost'),
        ('DAMAGED', 'Damaged'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')

    def save(self, *args, **kwargs):
        if self.pk:
            borrowed = self.requisition_set.filter(
                status__in=['PENDING', 'APPROVED']
            ).aggregate(total=Sum('quantity'))['total'] or 0
            self.available_quantity = max(self.total_quantity - borrowed, 0)
        else:
            self.available_quantity = self.total_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Requisition(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('RETURNED', 'Returned'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    borrower_name = models.CharField(max_length=150, blank=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField(blank=True)
    return_date = models.DateTimeField(null=True, blank=True) # Due Date
    actual_return_date = models.DateTimeField(null=True, blank=True)
    approve_date = models.DateTimeField(null=True, blank=True)
    reject_date = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    receive_comment = models.TextField(blank=True)
    
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='approved_requisitions', on_delete=models.SET_NULL, null=True, blank=True)
    rejected_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='rejected_requisitions', on_delete=models.SET_NULL, null=True, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_requisitions', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.equipment.name} ({self.status})"




# Signals to handle image deletion
import os
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, post_delete

@receiver(post_delete, sender=Equipment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `Equipment` object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)

@receiver(pre_save, sender=Equipment)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `Equipment` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = Equipment.objects.get(pk=instance.pk).image
    except Equipment.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if old_file and os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver([post_save, post_delete], sender=Requisition)
def recompute_equipment_available(sender, instance, **kwargs):
    eq = instance.equipment
    if not eq:
        return
    borrowed = Requisition.objects.filter(
        equipment=eq,
        status__in=['PENDING', 'APPROVED'],
    ).aggregate(total=Sum('quantity'))['total'] or 0
    new_available = max(eq.total_quantity - borrowed, 0)
    Equipment.objects.filter(pk=eq.pk).update(available_quantity=new_available)

