# Generated by Django 5.1.4 on 2025-01-12 12:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0005_case_complete_date_alter_case_case_detail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='complete_date',
            field=models.DateTimeField(blank=True),
        ),
    ]
