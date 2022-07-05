from django import forms
import re
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from validation.models import Issue, Recording, Phrase, SemanticClass

DEFAULT_MAX_LENGTH = 256


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
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control form-restrict"}),
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control form-restrict"}),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"class": "form-control form-restrict"}),
    )

    ROLE_CHOICES = [
        ("expert", "Language Expert"),
        ("linguist", "Linguist"),
        ("instructor", "Instructor"),
        ("learner", "Learner"),
    ]
    role = forms.ChoiceField(
        label="I am a(n)...",
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        required=False,
        help_text="""
        Experts are community members with an excellent understand of their target language <br>
        Linguists are expected to look at analyses and lemmas. <br>
        Instructors are those who are teaching others or advanced language learners.<br>
        Learners are students or other people currently learning the language.<br>
        """,
    )

    LANG_CHOICES = [
        ("maskwacis", "Maskwacîs"),
        ("tsuutina", "Tsuut'ina"),
        ("stoney-alexis", "Stoney Nakoda"),
        ("stoney-paul", "Stoney, Paul First Nation"),
        ("beaver", "Beaver"),
    ]

    language_variant = forms.MultipleChoiceField(
        label="I would like access to...",
        choices=LANG_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="""
        Please select all the languages you want access to with the role specified above. <br>
        If you leave this selection blank, you will be given learner level access to all languages.""",
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
    source_language = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    translation = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    analysis = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    comment = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control bottom-margin"}),
    )

    def __init__(self, *args, **kwargs):
        super(EditSegment, self).__init__(*args, **kwargs)
        self.fields["source_language"].label = "Entry"


class FlagSegment(forms.ModelForm):
    source_language_suggestion = forms.CharField(
        help_text="Use the space above to suggest a better spelling for the transcription",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control issue__textarea"}),
    )

    target_language_suggestion = forms.CharField(
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

    def __init__(self, *args, **kwargs):
        super(FlagSegment, self).__init__(*args, **kwargs)
        self.fields["source_language_suggestion"].label = "Target language suggestion"
        self.fields["target_language_suggestion"].label = "English suggestion"


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


class EditIssueWithPhrase(forms.ModelForm):
    transcription = forms.CharField(
        max_length=412,
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
    )

    translation = forms.CharField(
        max_length=412,
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Phrase
        fields = ["transcription", "translation"]


class RecordNewPhrase(forms.ModelForm):
    transcription = forms.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control issue__textarea"}),
    )

    translation = forms.CharField(
        max_length=DEFAULT_MAX_LENGTH,
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control issue__textarea"}),
    )

    file = forms.FileField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Recording
        fields = []

    def __init__(self, *args, **kwargs):
        super(RecordNewPhrase, self).__init__(*args, **kwargs)
        self.fields["transcription"].label = "Source language"
        self.fields["translation"].label = "English"
