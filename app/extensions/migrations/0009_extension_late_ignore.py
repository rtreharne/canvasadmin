# Generated by Django 3.2.20 on 2023-08-24 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extensions', '0008_auto_20230627_1215'),
    ]

    operations = [
        migrations.AddField(
            model_name='extension',
            name='late_ignore',
            field=models.BooleanField(default=False, verbose_name='Less than 5 minutes late?'),
        ),
    ]
