from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    full_name = forms.CharField(max_length=150, required=True)
    role = forms.ChoiceField(choices=UserProfile.Role.choices, initial=UserProfile.Role.USER)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-geo")

    class Meta:
        model = User
        fields = ("username", "full_name", "email", "password1", "password2", "role")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        first, *rest = self.cleaned_data["full_name"].split()
        user.first_name = first
        user.last_name = " ".join(rest)
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = self.cleaned_data["role"]
            profile.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"autofocus": True, "class": "form-geo"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-geo"}))


class ProfileForm(forms.ModelForm):
    full_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = UserProfile
        fields = ("role", "linked_agent")

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-geo")
        self.fields["full_name"].widget.attrs.setdefault("class", "form-geo")
        self.fields["email"].widget.attrs.setdefault("class", "form-geo")
        self.fields["role"].disabled = not self.user.is_superuser
        self.fields["linked_agent"].required = False
        self.fields["full_name"].initial = self.user.get_full_name()
        self.fields["email"].initial = self.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        full_name = self.cleaned_data.get("full_name", "").strip()
        if full_name:
            first, *rest = full_name.split()
            self.user.first_name = first
            self.user.last_name = " ".join(rest)
        self.user.email = self.cleaned_data["email"]
        if commit:
            self.user.save()
            profile.save()
        return profile
