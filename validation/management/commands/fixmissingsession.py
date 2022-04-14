from datetime import datetime

from django.core.management.base import BaseCommand

from librecval.recording_session import SessionID
from validation.models import (
    RecordingSession,
    Recording,
)


class Command(BaseCommand):
    help = "Add sessions to user-submitted entries"

    def handle(self, *args, **options):
        recordings = Recording.objects.filter(session_id=None)
        for rec in recordings:
            try:
                historical_recording = Recording.history.filter(id=rec.id).first()
                print(historical_recording.history_date)
                session_id = SessionID(
                    date=datetime.strptime(
                        historical_recording.history_date.split()[0], "%Y-%m-%d"
                    ),
                    time_of_day=None,
                    subsession=None,
                    location=None,
                )
            except AttributeError as e:
                session_id = SessionID(
                    date=datetime.strptime("2022-04-14", "%Y-%m-%d"),
                    time_of_day=None,
                    subsession=None,
                    location=None,
                )

            rec_session, created = RecordingSession.get_or_create_by_session_id(
                session_id
            )
            rec.session_id = rec_session.id
            rec.save()
