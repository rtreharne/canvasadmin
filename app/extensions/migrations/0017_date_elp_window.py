# Generated by Django 3.2.25 on 2025-01-14 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extensions', '0016_date_extension_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='date',
            name='elp_window',
            field=models.IntegerField(default=21, help_text='ELP window in days.'),
        ),
    ]
