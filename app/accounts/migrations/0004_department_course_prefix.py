# Generated by Django 3.2.17 on 2023-02-02 14:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20230202_1020'),
    ]

    operations = [
        migrations.AddField(
            model_name='department',
            name='course_prefix',
            field=models.CharField(blank=True, max_length=28, null=True),
        ),
    ]
