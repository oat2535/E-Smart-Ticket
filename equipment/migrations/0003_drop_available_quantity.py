from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0002_anonymous_request'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='equipment',
            name='available_quantity',
        ),
    ]
