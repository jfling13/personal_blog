# Generated by Django 4.2.4 on 2023-08-28 19:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='post',
            old_name='pub_time',
            new_name='publish_date',
        ),
    ]