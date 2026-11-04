from django import forms
from .models import TicketType


class TicketTypeForm(forms.ModelForm):
    sales_start = forms.DateTimeField(
        required=False,
        label="Sales Start Date",
        help_text="Leave blank to start selling immediately.",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-input"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    sales_end = forms.DateTimeField(
        required=False,
        label="Sales End Date",
        help_text="Leave blank to sell until the event starts.",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-input"}),
        input_formats=["%Y-%m-%dT%H:%M"],
    )

    class Meta:
        model = TicketType
        fields = ("name", "description", "price", "quantity", "max_per_order", "sales_start", "sales_end", "is_active")
        labels = {
            "quantity": "Total Quantity Available",
            "max_per_order": "Max Tickets Per Order",
            "is_active": "Active (visible and on sale)",
        }
        help_texts = {
            "quantity": "Total number of tickets for sale. Set to 0 for unlimited.",
            "max_per_order": "Maximum tickets one person can buy in a single order.",
            "price": "Set to 0.00 for a free ticket.",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. General Admission, VIP, Early Bird"}),
            "description": forms.Textarea(attrs={"class": "form-input", "rows": 3, "placeholder": "Optional description of what this ticket includes..."}),
            "price": forms.NumberInput(attrs={"class": "form-input", "min": "0", "step": "0.01", "placeholder": "0.00"}),
            "quantity": forms.NumberInput(attrs={"class": "form-input", "min": "0", "placeholder": "e.g. 100"}),
            "max_per_order": forms.NumberInput(attrs={"class": "form-input", "min": "1", "value": "10"}),
        }

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty is None:
            raise forms.ValidationError("Please enter a quantity. Use 0 for unlimited.")
        return qty

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None or price < 0:
            raise forms.ValidationError("Price must be 0 or more.")
        return price