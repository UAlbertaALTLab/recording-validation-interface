from django import forms
import re
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User


class Login(forms.Form):
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "style": "max-width: 15rem;"}
        ),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "style": "max-width: 15rem;"}
        ),
    )


class Register(forms.Form):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "style": "max-width: 15rem;"}
        ),
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "style": "max-width: 15rem;"}
        ),
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "style": "max-width: 15rem;"}
        ),
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "style": "max-width: 15rem;"}
        ),
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
