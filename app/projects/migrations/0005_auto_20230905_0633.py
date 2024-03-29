# Generated by Django 3.2.20 on 2023-09-05 06:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20230202_1455'),
        ('projects', '0004_alter_project_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='module',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
        migrations.AddField(
            model_name='project',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
        migrations.AddField(
            model_name='projectarea',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
        migrations.AddField(
            model_name='projectkeyword',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
        migrations.AddField(
            model_name='projecttype',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
        migrations.AddField(
            model_name='staff',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
        migrations.AddField(
            model_name='student',
            name='school',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department'),
        ),
    ]
