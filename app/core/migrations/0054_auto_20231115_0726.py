# Generated by Django 3.2.22 on 2023-11-15 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0053_alter_submission_marker_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='support_plan_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='submission',
            name='marker_email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]