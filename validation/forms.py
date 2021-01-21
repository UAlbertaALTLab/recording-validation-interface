from django import forms


class EditSegment(forms.Form):
    cree = forms.CharField(required=False, widget=forms.TextInput)
    transl = forms.CharField(required=False, widget=forms.TextInput)
    analysis = forms.CharField(required=False, widget=forms.TextInput)
