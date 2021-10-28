# Generated by Django 2.2.24 on 2021-10-19 19:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0019_issue_target_language_suggestion"),
    ]

    operations = [
        migrations.RenameField(
            model_name="speaker",
            old_name="crk_bio_audio",
            new_name="source_bio_audio",
        ),
        migrations.RenameField(
            model_name="speaker",
            old_name="crk_bio_text",
            new_name="source_bio_text",
        ),
        migrations.RenameField(
            model_name="speaker",
            old_name="eng_bio_audio",
            new_name="target_bio_audio",
        ),
        migrations.RenameField(
            model_name="speaker",
            old_name="eng_bio_text",
            new_name="target_bio_text",
        ),
    ]