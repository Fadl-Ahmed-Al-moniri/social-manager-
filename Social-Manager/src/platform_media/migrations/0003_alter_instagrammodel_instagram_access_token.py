# Generated by Django 5.1.1 on 2025-03-05 23:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('platform_media', '0002_instagrammodel_facebook_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instagrammodel',
            name='instagram_access_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
