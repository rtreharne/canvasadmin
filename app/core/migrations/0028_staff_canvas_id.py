# Generated by Django 3.2.17 on 2023-02-07 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_staff'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='canvas_id',
            field=models.IntegerField(blank=True, null=True, unique=True),
        ),
    ]
