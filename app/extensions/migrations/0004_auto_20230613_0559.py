# Generated by Django 3.2.18 on 2023-06-13 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extensions', '0003_auto_20230526_0502'),
    ]

    operations = [
        migrations.AddField(
            model_name='extension',
            name='files',
            field=models.FileField(blank=True, null=True, upload_to='extensions/'),
        ),
        migrations.AddField(
            model_name='extension',
            name='reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
