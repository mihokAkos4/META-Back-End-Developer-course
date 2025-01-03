# Generated by Django 4.2.17 on 2024-12-29 20:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField()),
                ('title', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.SlugField()),
                ('price', models.CharField(max_length=255)),
                ('inventory', models.DecimalField(decimal_places=2, max_digits=6)),
                ('category', models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='LittleLemonDRF.category')),
            ],
        ),
    ]
