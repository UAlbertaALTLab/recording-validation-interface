# Generated by Django 2.1.2 on 2018-10-24 21:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('validation', '0015_historicalphrase'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recording',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(help_text='The time at which this recording starts')),
                ('quality', models.CharField(choices=[('clean', 'Clean'), ('unusable', 'Unusable')], help_text='Is the recording clean and usable publically?', max_length=8)),
                ('phrase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='validation.Phrase')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='validation.RecordingSession')),
                ('speaker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='validation.Speaker')),
            ],
        ),
    ]
