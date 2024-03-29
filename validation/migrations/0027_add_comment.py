# Generated by Django 2.2.26 on 2022-05-03 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0026_add_i3"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalphrase",
            name="comment",
            field=models.CharField(
                blank=True, help_text="Comments about the phrase", max_length=2048
            ),
        ),
        migrations.AddField(
            model_name="phrase",
            name="comment",
            field=models.CharField(
                blank=True, help_text="Comments about the phrase", max_length=2048
            ),
        ),
    ]
