# Generated by Django 3.2.23 on 2024-03-01 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('extensions', '0012_extension_submitted_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='extension',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=128),
        ),
    ]
