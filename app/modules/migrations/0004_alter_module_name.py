# Generated by Django 3.2.18 on 2023-03-21 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('modules', '0003_alter_module_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='module',
            name='name',
            field=models.CharField(max_length=256, verbose_name='Module Title'),
        ),
    ]
