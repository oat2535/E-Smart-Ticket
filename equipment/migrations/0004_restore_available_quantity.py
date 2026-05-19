from django.db import migrations, models
from django.db.models import Sum


def initialize_available_quantity(apps, schema_editor):
    Equipment = apps.get_model('equipment', 'Equipment')
    Requisition = apps.get_model('equipment', 'Requisition')
    for eq in Equipment.objects.all():
        borrowed = Requisition.objects.filter(
            equipment=eq,
            status__in=['PENDING', 'APPROVED'],
        ).aggregate(total=Sum('quantity'))['total'] or 0
        eq.available_quantity = max(eq.total_quantity - borrowed, 0)
        eq.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('equipment', '0003_drop_available_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipment',
            name='available_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(initialize_available_quantity, noop_reverse),
    ]
