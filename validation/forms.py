from django import forms


class Login(forms.Form):
    username = forms.CharField(required=False, widget=forms.TextInput)
    password = forms.CharField(required=False, widget=forms.PasswordInput)


class Register(forms.Form):
    username = forms.CharField(required=False, widget=forms.TextInput)
    password = forms.CharField(required=False, widget=forms.PasswordInput)
