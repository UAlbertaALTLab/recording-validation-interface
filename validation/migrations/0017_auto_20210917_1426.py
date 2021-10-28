# Generated by Django 2.2.24 on 2021-09-17 20:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0016_merge_20210916_1740"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalphrase",
            name="origin",
            field=models.CharField(
                choices=[
                    ("MD", "Maskwacîs Dictionary"),
                    ("OS", "Onespot-Sapir Dictionary"),
                    ("new", "New word"),
                ],
                default="new",
                help_text="How did we get this phrase?",
                max_length=3,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="phrase",
            name="origin",
            field=models.CharField(
                choices=[
                    ("MD", "Maskwacîs Dictionary"),
                    ("OS", "Onespot-Sapir Dictionary"),
                    ("new", "New word"),
                ],
                default="new",
                help_text="How did we get this phrase?",
                max_length=3,
                null=True,
            ),
        ),
    ]