# Generated by Django 3.2.17 on 2023-02-05 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_alter_student_canvas_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='pc_graded',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
