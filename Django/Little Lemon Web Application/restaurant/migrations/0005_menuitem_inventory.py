# Generated by Django 5.1.4 on 2025-01-03 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0004_menuitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='inventory',
            field=models.SmallIntegerField(default=0),
            preserve_default=False,
        ),
    ]