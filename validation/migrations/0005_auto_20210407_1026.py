# Generated by Django 2.2.19 on 2021-04-07 16:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0004_auto_20210326_1039"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="issue",
            name="other_reason",
        ),
        migrations.AddField(
            model_name="issue",
            name="recording",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="validation.Recording",
            ),
        ),
        migrations.AddField(
            model_name="issue",
            name="suggested_cree",
            field=models.CharField(
                blank=True,
                help_text="The Cree spelling suggested by the validator",
                max_length=1024,
            ),
        ),
        migrations.AddField(
            model_name="issue",
            name="suggested_english",
            field=models.CharField(
                blank=True,
                help_text="The English spelling suggested by the validator",
                max_length=1024,
            ),
        ),
        migrations.AlterField(
            model_name="issue",
            name="phrase",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="validation.Phrase",
            ),
        ),
    ]
