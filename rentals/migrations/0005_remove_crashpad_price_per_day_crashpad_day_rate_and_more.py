# Generated by Django 4.2.18 on 2025-02-24 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rentals', '0004_remove_crashpad_capacity_alter_crashpad_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='crashpad',
            name='price_per_day',
        ),
        migrations.AddField(
            model_name='crashpad',
            name='day_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='crashpad',
            name='fourteen_day_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name='crashpad',
            name='seven_day_rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
