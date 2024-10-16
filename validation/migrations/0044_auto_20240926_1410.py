# Generated by Django 4.2.15 on 2024-09-26 20:10

from django.db import migrations
from validation.management.rapidwords_initialize import map_function_to_all_rapidwords


def generate_rapidword_classes(apps, schema_editor):
    SemanticClass = apps.get_model("validation", "SemanticClass")

    def import_rw(rapidword):
        return SemanticClass(collection="rapidwords", classification=rapidword)

    SemanticClass.objects.bulk_create(map_function_to_all_rapidwords(import_rw))
    return


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0043_semanticclass_and_more"),
    ]

    operations = [migrations.RunPython(generate_rapidword_classes)]
