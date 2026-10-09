from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

User = get_user_model()


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Used only for account recovery.")
    wants_to_write = forms.BooleanField(
        required=False,
        label="I want to write and publish posts",
        help_text="Readers can comment and like. Authors can also write posts.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.ALLOW_AUTHOR_SIGNUP:
            del self.fields["wants_to_write"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            if self.cleaned_data.get("wants_to_write"):
                group, _ = Group.objects.get_or_create(name=settings.AUTHORS_GROUP)
                user.groups.add(group)
        return user
