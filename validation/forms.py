from django import forms


class Login(forms.Form):
    username = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "style": "max-width: 15rem;"}
        ),
    )
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "style": "max-width: 15rem;"}
        ),
    )


class Register(forms.Form):
    username = forms.CharField(required=False, widget=forms.TextInput)
    password = forms.CharField(required=False, widget=forms.PasswordInput)
