# Generated by Django 3.2.17 on 2023-02-04 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_student_programme'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='canvas_id',
            field=models.IntegerField(default=1, unique=True),
            preserve_default=False,
        ),
    ]
