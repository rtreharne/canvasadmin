# Generated by Django 3.2.20 on 2023-09-25 11:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0047_assignment_rollover_to_course'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='previous_term_assignment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='core.assignment'),
        ),
    ]
