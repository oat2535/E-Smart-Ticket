# Generated by Django 5.1.4 on 2025-01-12 12:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0008_alter_case_complete_date_alter_case_receive_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='complete_date',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='case',
            name='receive_date',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
