# Generated by Django 2.2.24 on 2021-10-28 21:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0014_speaker_image"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="speaker",
            name="image",
        ),
    ]
