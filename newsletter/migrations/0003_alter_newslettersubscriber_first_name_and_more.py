# Generated by Django 4.2.18 on 2025-03-02 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0002_newslettermail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newslettersubscriber',
            name='first_name',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='newslettersubscriber',
            name='last_name',
            field=models.CharField(max_length=100),
        ),
    ]
