# Generated by Django 2.2.26 on 2022-05-12 21:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0027_add_comment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicalphrase",
            name="comment",
            field=models.CharField(
                blank=True,
                help_text="Comments about the phrase",
                max_length=2048,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="historicalrecording",
            name="was_user_submitted",
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text="This recording was submitted online by a user, but is now approved for use",
            ),
        ),
        migrations.AlterField(
            model_name="phrase",
            name="comment",
            field=models.CharField(
                blank=True,
                help_text="Comments about the phrase",
                max_length=2048,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="recording",
            name="was_user_submitted",
            field=models.BooleanField(
                blank=True,
                default=False,
                help_text="This recording was submitted online by a user, but is now approved for use",
            ),
        ),
    ]
