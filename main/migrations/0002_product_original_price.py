# Generated by Django 5.0.4 on 2024-11-30 22:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='original_price',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]