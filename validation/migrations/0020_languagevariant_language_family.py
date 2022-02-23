# Generated by Django 2.2.26 on 2022-02-22 22:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0019_add_auto_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="languagevariant",
            name="language_family",
            field=models.CharField(
                blank=True,
                help_text="The larger language family that this variant belongs to, if any",
                max_length=256,
                null=True,
            ),
        ),
    ]
