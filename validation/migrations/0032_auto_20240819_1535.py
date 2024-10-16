# Generated by Django 3.2.25 on 2024-08-19 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0031_auto_20240612_1513"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="historicalphrase",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical phrase",
                "verbose_name_plural": "historical phrases",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalrecording",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical recording",
                "verbose_name_plural": "historical recordings",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalsemanticclass",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical semantic class",
                "verbose_name_plural": "historical semantic classs",
            },
        ),
        migrations.AlterField(
            model_name="historicalphrase",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalrecording",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name="historicalsemanticclass",
            name="history_date",
            field=models.DateTimeField(db_index=True),
        ),
    ]
