from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0004_restore_available_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='comment',
            field=models.TextField(blank=True),
        ),
    ]
