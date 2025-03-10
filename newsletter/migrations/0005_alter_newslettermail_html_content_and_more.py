# Generated by Django 4.2.18 on 2025-03-02 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newsletter', '0004_remove_newslettersubscriber_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newslettermail',
            name='html_content',
            field=models.TextField(help_text='You can use template variables like {{ user.first_name }}, {{ site_url }}, etc.'),
        ),
        migrations.AlterField(
            model_name='newslettermail',
            name='sent_to',
            field=models.ManyToManyField(blank=True, related_name='received_newsletters', to='newsletter.newslettersubscriber'),
        ),
    ]
