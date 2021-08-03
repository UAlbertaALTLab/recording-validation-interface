import json
import secrets

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.core.management.base import BaseCommand

from validation.models import Phrase


class Command(BaseCommand):
    help = """Ensure that the test db exists and is properly set up.
    If it does not exist, it will be created. If it needs to be migrated, it
    will be migrated. If assorted other things need to be in there, they will be
    added if missing.
    """

    def handle(self, *args, **options):

        call_command("migrate", verbosity=0)

        create_test_users()
        import_test_phrases()


def import_test_phrases():
    if not Phrase.objects.exists():
        print("No phrases found, generating")
        call_command(
            "loaddata",
            "speaker_info",
            "test_recordingsession",
            "test_phrases",
            "test_recordings",
            "test_issues",
        )


def create_test_user(username, group_name):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password("1234567890")
    user.save()
    group, _ = Group.objects.get_or_create(name=group_name)
    group.user_set.add(user)


def create_test_users():
    for username in ["expert", "instructor", "linguist", "learner"]:
        create_test_user(username, username.title())
