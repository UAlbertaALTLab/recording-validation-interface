# Generated by Django 2.2.8 on 2019-12-05 22:08

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("validation", "0001_initial"),
        ("validation", "0002_recordingsession_date"),
        ("validation", "0003_auto_20181018_1242"),
        ("validation", "0004_auto_20181018_1258"),
        ("validation", "0005_auto_20181018_1301"),
        ("validation", "0006_auto_20181018_1310"),
        ("validation", "0007_auto_20181018_1313"),
        ("validation", "0008_auto_20181018_1319"),
        ("validation", "0009_auto_20181018_1322"),
        ("validation", "0010_auto_20181018_1337"),
        ("validation", "0011_speaker"),
        ("validation", "0012_phrase"),
        ("validation", "0013_phrase_origin"),
        ("validation", "0014_auto_20181019_0856"),
        ("validation", "0015_historicalphrase"),
        ("validation", "0016_recording"),
        ("validation", "0017_auto_20181024_1543"),
        ("validation", "0018_historicalrecording"),
        ("validation", "0019_auto_20181024_1601"),
        ("validation", "0020_auto_20181101_1032"),
        ("validation", "0021_auto_20181101_1104"),
        ("validation", "0022_auto_20181101_1459"),
        ("validation", "0023_auto_20181101_1828"),
        ("validation", "0024_auto_20181210_1342"),
        ("validation", "0025_auto_20181221_1129"),
    ]

    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="RecordingSession",
            fields=[
                (
                    "id",
                    models.CharField(max_length=19, primary_key=True, serialize=False),
                ),
                ("date", models.DateField(help_text="The day the session occured.")),
                (
                    "time_of_day",
                    models.CharField(
                        blank=True,
                        choices=[("AM", "AM"), ("PM", "PM")],
                        default="",
                        help_text="The time of day the session occured. May be empty.",
                        max_length=2,
                    ),
                ),
                (
                    "location",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("DS", "DS"),
                            ("US", "US"),
                            ("KCH", "KCH"),
                            ("OFF", "OFF"),
                        ],
                        default="",
                        help_text="The location of the recordings. May be empty.",
                        max_length=3,
                    ),
                ),
                (
                    "subsession",
                    models.IntegerField(
                        blank=True,
                        help_text="The 'subsession' number, if applicable.",
                        null=True,
                    ),
                ),
            ],
            options={"unique_together": set()},
        ),
        migrations.CreateModel(
            name="Speaker",
            fields=[
                (
                    "code",
                    models.CharField(
                        help_text="Short code assigned to speaker in the ellicitation metadata.",
                        max_length=8,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "full_name",
                    models.CharField(
                        help_text="The speaker's full name.", max_length=128
                    ),
                ),
                (
                    "gender",
                    models.CharField(
                        choices=[("M", "Male"), ("F", "Female")],
                        help_text="Gender of the voice.",
                        max_length=1,
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Phrase",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "transcription",
                    models.CharField(
                        help_text="The transciption of the Cree phrase.", max_length=256
                    ),
                ),
                (
                    "translation",
                    models.CharField(
                        help_text="The English translation of the phrase.",
                        max_length=256,
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[("word", "Word"), ("sentence", "Sentence")],
                        help_text="Is this phrase a word or a sentence?",
                        max_length=8,
                    ),
                ),
                (
                    "validated",
                    models.BooleanField(
                        default=False, help_text="Has this phrase be validated?"
                    ),
                ),
                (
                    "origin",
                    models.CharField(
                        choices=[("MD", "Maskwacîs Dictionary"), ("new", "New word")],
                        default="new",
                        help_text="How did we get this phrase?",
                        max_length=3,
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="HistoricalPhrase",
            fields=[
                (
                    "id",
                    models.IntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                (
                    "transcription",
                    models.CharField(
                        help_text="The transciption of the Cree phrase.", max_length=256
                    ),
                ),
                (
                    "translation",
                    models.CharField(
                        help_text="The English translation of the phrase.",
                        max_length=256,
                    ),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[("word", "Word"), ("sentence", "Sentence")],
                        help_text="Is this phrase a word or a sentence?",
                        max_length=8,
                    ),
                ),
                (
                    "validated",
                    models.BooleanField(
                        default=False, help_text="Has this phrase be validated?"
                    ),
                ),
                (
                    "origin",
                    models.CharField(
                        choices=[("MD", "Maskwacîs Dictionary"), ("new", "New word")],
                        default="new",
                        help_text="How did we get this phrase?",
                        max_length=3,
                        null=True,
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                ("history_date", models.DateTimeField()),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "historical phrase",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="HistoricalRecording",
            fields=[
                ("id", models.CharField(db_index=True, max_length=64)),
                (
                    "timestamp",
                    models.IntegerField(
                        help_text="The offset (in milliseconds) when the phrase starts in the master file"
                    ),
                ),
                (
                    "quality",
                    models.CharField(
                        blank=True,
                        choices=[("clean", "Clean"), ("unusable", "Unusable")],
                        help_text="Is the recording clean? Is it suitable to use publicly?",
                        max_length=8,
                    ),
                ),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                ("history_date", models.DateTimeField()),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "phrase",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="validation.Phrase",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="validation.RecordingSession",
                    ),
                ),
                (
                    "speaker",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="validation.Speaker",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical recording",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": "history_date",
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="Recording",
            fields=[
                (
                    "id",
                    models.CharField(max_length=64, primary_key=True, serialize=False),
                ),
                (
                    "timestamp",
                    models.IntegerField(
                        help_text="The offset (in milliseconds) when the phrase starts in the master file"
                    ),
                ),
                (
                    "quality",
                    models.CharField(
                        blank=True,
                        choices=[("clean", "Clean"), ("unusable", "Unusable")],
                        help_text="Is the recording clean? Is it suitable to use publicly?",
                        max_length=8,
                    ),
                ),
                (
                    "phrase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="validation.Phrase",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="validation.RecordingSession",
                    ),
                ),
                (
                    "speaker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="validation.Speaker",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="phrase",
            index=models.Index(fields=["transcription"], name="transcription_idx"),
        ),
        migrations.AddField(
            model_name="historicalphrase",
            name="fuzzy_transcription",
            field=models.CharField(
                default="<UNINDEXABLE>",
                editable=False,
                help_text="The indexed form of the transcription to facilitate fuzzy matching (automatically managed).",
                max_length=256,
            ),
        ),
        migrations.AddField(
            model_name="phrase",
            name="fuzzy_transcription",
            field=models.CharField(
                default="<UNINDEXABLE>",
                editable=False,
                help_text="The indexed form of the transcription to facilitate fuzzy matching (automatically managed).",
                max_length=256,
            ),
        ),
        migrations.AddIndex(
            model_name="phrase",
            index=models.Index(
                fields=["fuzzy_transcription"], name="fuzzy_transcription_idx"
            ),
        ),
    ]