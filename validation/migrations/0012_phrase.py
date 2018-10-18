# Generated by Django 2.1.2 on 2018-10-18 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('validation', '0011_speaker'),
    ]

    operations = [
        migrations.CreateModel(
            name='Phrase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transcription', models.CharField(help_text='The transciption of the Cree phrase.', max_length=256)),
                ('translation', models.CharField(help_text='The English translation of the phrase.', max_length=256)),
                ('kind', models.CharField(choices=[('word', 'Word'), ('sentence', 'Sentence')], help_text='Is this phrase a word or a sentence?', max_length=8)),
                ('validated', models.BooleanField(default=False, help_text='Has this phrase be validated?')),
            ],
        ),
    ]
