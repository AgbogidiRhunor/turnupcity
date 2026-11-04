from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class SignupForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50, required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "First name"})
    )
    last_name = forms.CharField(
        max_length=50, required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Last name"})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-input", "placeholder": "you@example.com"})
    )
    username = forms.CharField(
        max_length=150, required=True,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Choose a username"})
    )
    role = forms.ChoiceField(
        choices=[
            (User.ROLE_GUEST, "Attendee — I want to buy tickets"),
            (User.ROLE_ORGANIZER, "Organizer — I want to host events"),
            (User.ROLE_STAFF, "Staff — I want to work at events"),
        ],
        widget=forms.Select(attrs={"class": "form-input"})
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Create a password"})
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "Repeat your password"})
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "username", "role", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "class": "form-input",
            "autofocus": True,
            "placeholder": "you@example.com"
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-input",
            "placeholder": "Your password"
        })
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "phone", "bio", "avatar")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "username": forms.TextInput(attrs={"class": "form-input"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "placeholder": "+1 555 000 0000"}),
            "bio": forms.Textarea(attrs={"class": "form-input", "rows": 4,
                                         "placeholder": "Tell us a bit about yourself..."}),
        }
