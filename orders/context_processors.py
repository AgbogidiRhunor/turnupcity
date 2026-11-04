from django.conf import settings


def paystack(request):
    """Make Paystack public key available in all templates."""
    return {
        'PAYSTACK_PUBLIC_KEY': getattr(settings, 'PAYSTACK_PUBLIC_KEY', ''),
    }
