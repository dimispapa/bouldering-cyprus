# Generated by Django 5.1.4 on 2025-01-29 13:58

import django_summernote.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='description',
            field=django_summernote.fields.SummernoteTextField(blank=True),
        ),
    ]
