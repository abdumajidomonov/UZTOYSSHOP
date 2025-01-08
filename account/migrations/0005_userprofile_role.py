# Generated by Django 5.0.4 on 2024-11-30 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_alter_userprofile_picture'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='role',
            field=models.CharField(blank=True, choices=[('admin', 'Admin'), ('seller', 'Seller'), ('client', 'Client')], default='client', max_length=6, null=True, verbose_name='Role'),
        ),
    ]
