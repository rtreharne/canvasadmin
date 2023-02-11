# Generated by Django 3.2.17 on 2023-02-02 13:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20230202_1020'),
        ('core', '0011_remove_assignment_rubric'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assignment',
            name='assignment_id',
            field=models.IntegerField(editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='course',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='core.course'),
        ),
        migrations.AlterField(
            model_name='assignment',
            name='department',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
    ]
