# Generated by Django 4.2.15 on 2024-10-02 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0052_alter_phrase_semantic_classes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="phrase",
            name="semantic_classes",
            field=models.ManyToManyField(
                blank=True,
                through="validation.SemanticClassAnnotation",
                to="validation.semanticclass",
            ),
        ),
    ]
