from django import forms
import re
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from validation.models import Issue, Recording, Phrase


class Login(forms.Form):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-restrict"}),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control form-restrict"}),
    )


class Register(forms.Form):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-restrict"}),
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-restrict"}),
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-restrict"}),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control form-restrict"}),
    )

    CHOICES = [
        ("expert", "Language Expert"),
        ("linguist", "Linguist"),
        ("instructor", "Instructor"),
        ("learner", "Learner"),
    ]
    role = forms.ChoiceField(
        label="I am a(n)...",
        choices=CHOICES,
        widget=forms.RadioSelect,
        required=False,
        help_text="""
        Community members are considered language experts or active members in a Cree-speaking community. <br>
        Linguists are expected to look at analyses and lemmas. <br>
        Instructors are those who are teaching others or advanced language learners.<br>
        Learners are students or other people currently learning the language.<br>
        """,
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if not re.search(
            r"^\w+$", username
        ):  # checks if all the characters in username are in the regex. If they aren't, it returns None
            raise forms.ValidationError(
                "Username can only contain alphanumeric characters and the underscore."
            )
        try:
            User.objects.get(
                username=username
            )  # this raises an ObjectDoesNotExist exception if it doesn't find a user with that username
        except ObjectDoesNotExist:
            return username  # if username doesn't exist, this is good. We can create the username
        raise forms.ValidationError("Username is already taken.", code="invalid")


class EditSegment(forms.Form):
    cree = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    translation = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    analysis = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control bottom-margin"}),
    )


class FlagSegment(forms.ModelForm):
    cree_suggestion = forms.CharField(
        help_text="Use the space above to suggest a better Cree spelling",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control issue__textarea"}),
    )

    english_suggestion = forms.CharField(
        help_text="Use the space above to suggest a better English word or phrase",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control issue__textarea"}),
    )

    comment = forms.CharField(
        help_text="Use the space above to provide an example or make a few notes about why you're reporting an issue "
        "with this entry",
        required=False,
        widget=forms.Textarea(
            attrs={"class": "form-control bottom-margin issue__textarea"}
        ),
    )

    phrase_id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Issue
        fields = ["phrase_id"]


class EditIssueWithRecording(forms.ModelForm):
    phrase = forms.CharField(
        widget=forms.Textarea(),
        required=False,
        help_text="What word or phrase this recording is actually for",
    )

    class Meta:
        model = Recording
        fields = ["speaker"]
        help_texts = {
            "speaker": "\n",
        }


ALLOWED_TRANSCRIPTION_CHARACTERS = set("ptkcshmn yw rl eêiîoôaâ -")


class EditIssueWithPhrase(forms.ModelForm):
    transcription = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-restrict"}),
    )

    translation = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control form-restrict"}),
    )

    class Meta:
        model = Phrase
        fields = ["transcription", "translation"]

    def clean_transcription(self):
        transcription = self.cleaned_data.get("transcription")

        if not ALLOWED_TRANSCRIPTION_CHARACTERS.issuperset(transcription):
            print("doot")
            raise forms.ValidationError(
                f"Transcriptions can only contain these characters: {ALLOWED_TRANSCRIPTION_CHARACTERS}"
            )
