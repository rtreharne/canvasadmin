# Generated by Django 3.2.17 on 2023-02-02 16:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20230202_1455'),
        ('logs', '0005_alter_assignmentlog_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmentlog',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
    ]
