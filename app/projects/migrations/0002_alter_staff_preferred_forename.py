# Generated by Django 3.2.20 on 2023-07-18 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staff',
            name='preferred_forename',
            field=models.CharField(blank=True, default=None, max_length=25, null=True),
        ),
    ]
