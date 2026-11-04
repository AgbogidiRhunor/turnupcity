from django import forms
from .models import Event, Coupon


class EventForm(forms.ModelForm):
    start_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    end_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    refund_deadline = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Event
        fields = (
            'title', 'category', 'description', 'banner',
            'venue_name', 'venue_address', 'venue_map_link', 'city', 'country',
            'start_date', 'end_date', 'refund_deadline',
            'capacity', 'is_private'
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 6}),
            'venue_name': forms.TextInput(attrs={'class': 'form-input'}),
            'venue_address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'venue_map_link': forms.URLInput(attrs={'class': 'form-input'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class CouponForm(forms.ModelForm):
    valid_from = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    valid_until = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )

    class Meta:
        model = Coupon
        fields = ('code', 'discount_type', 'discount_value', 'max_uses', 'valid_from', 'valid_until', 'is_active')
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-input'}),
            'discount_type': forms.Select(attrs={'class': 'form-input'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-input'}),
            'max_uses': forms.NumberInput(attrs={'class': 'form-input'}),
        }
