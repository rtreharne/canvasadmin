# Generated by Django 3.2.23 on 2024-03-04 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extensions', '0014_extension_reject_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='extension',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]