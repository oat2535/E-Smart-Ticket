# Generated by Django 5.1.4 on 2025-02-06 16:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0014_alter_case_feedback_alter_case_score'),
    ]

    operations = [
        migrations.RenameField(
            model_name='case',
            old_name='cancel_date',
            new_name='satisfied_date',
        ),
    ]
