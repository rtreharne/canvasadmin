# Generated by Django 3.2.20 on 2023-08-14 09:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_course_resit_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='posted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
