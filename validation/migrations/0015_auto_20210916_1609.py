# Generated by Django 2.2.24 on 2021-09-16 22:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0014_auto_20210916_1608"),
    ]

    operations = [
        migrations.RenameField(
            model_name="historicalphrase",
            old_name="word_id",
            new_name="osid",
        ),
        migrations.RenameField(
            model_name="phrase",
            old_name="word_id",
            new_name="osid",
        ),
    ]