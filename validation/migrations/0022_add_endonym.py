# Generated by Django 2.2.26 on 2022-03-31 19:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0021_add_is_best"),
    ]

    operations = [
        migrations.AddField(
            model_name="languagevariant",
            name="endonym",
            field=models.CharField(
                blank=True,
                help_text="The name of the language in the language itself",
                max_length=256,
                null=True,
            ),
        ),
    ]