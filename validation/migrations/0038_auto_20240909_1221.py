# Generated by Django 4.2.15 on 2024-09-09 18:21

from django.db import migrations


def create_data(apps, schema_editor):
    Collection = apps.get_model("validation", "Collection")
    Collection.objects.create(code="DEFAULT", name="Default Collection")


class Migration(migrations.Migration):

    dependencies = [
        ("validation", "0037_collection"),
    ]

    operations = [migrations.RunPython(create_data)]
