# Generated by Django 2.2.24 on 2021-07-09 17:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0007_wrong_word_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="issue",
            name="bad_cree",
        ),
        migrations.RemoveField(
            model_name="issue",
            name="bad_english",
        ),
        migrations.RemoveField(
            model_name="issue",
            name="bad_recording",
        ),
        migrations.RemoveField(
            model_name="issue",
            name="other",
        ),
    ]
