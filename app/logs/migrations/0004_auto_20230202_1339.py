# Generated by Django 3.2.17 on 2023-02-02 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0003_rename_key_assignmentlog_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmentlog',
            name='course',
            field=models.CharField(default='asdf', max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='assignmentlog',
            name='assignment',
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name='assignmentlog',
            name='from_value',
            field=models.CharField(max_length=128, null=True),
        ),
        migrations.AlterField(
            model_name='assignmentlog',
            name='to_value',
            field=models.CharField(max_length=128, null=True),
        ),
    ]
