# Generated by Django 5.1.4 on 2024-12-25 12:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0002_category_department_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='category',
            old_name='department_id',
            new_name='department',
        ),
    ]
