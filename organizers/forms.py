from django import forms
from django.utils.text import slugify
from .models import OrganizerProfile, StaffRequest


class OrganizerProfileForm(forms.ModelForm):
    class Meta:
        model = OrganizerProfile
        fields = ('organization_name', 'description', 'logo', 'website', 'twitter', 'instagram')
        widgets = {
            'organization_name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'website': forms.URLInput(attrs={'class': 'form-input'}),
            'twitter': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '@handle'}),
            'instagram': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '@handle'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.organization_name)
        if commit:
            instance.save()
        return instance


class StaffRequestForm(forms.ModelForm):
    class Meta:
        model = StaffRequest
        fields = ('message',)
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-input', 'rows': 4,
                                             'placeholder': 'Tell the organizer why you want to work for them...'}),
        }
