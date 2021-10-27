# Generated by Django 2.2.24 on 2021-10-19 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0013_make_user_nullable_on_speaker"),
    ]

    operations = [
        migrations.AddField(
            model_name="speaker",
            name="image",
            field=models.ImageField(blank=True, upload_to="data/speakers/images/"),
        ),
    ]
