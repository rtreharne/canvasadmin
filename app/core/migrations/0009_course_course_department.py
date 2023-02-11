# Generated by Django 3.2.17 on 2023-02-02 05:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20230202_0539'),
        ('core', '0008_rename_open_at_assignment_unlock_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='course_department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
    ]
