from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0005_requisition_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='requisition',
            name='receive_comment',
            field=models.TextField(blank=True),
        ),
    ]
