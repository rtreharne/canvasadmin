# Generated by Django 3.2.17 on 2023-02-07 07:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20230202_1455'),
        ('logs', '0006_assignmentlog_department'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubmissionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student', models.CharField(max_length=128)),
                ('submission', models.CharField(max_length=128)),
                ('course', models.CharField(max_length=128)),
                ('request', models.CharField(choices=[('UPDATE', 'Update'), ('DELETE', 'Delete'), ('CREATE', 'Create')], max_length=128)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('field', models.CharField(blank=True, max_length=128, null=True)),
                ('from_value', models.CharField(max_length=128, null=True)),
                ('to_value', models.CharField(max_length=128, null=True)),
                ('department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='accounts.department')),
            ],
        ),
    ]
