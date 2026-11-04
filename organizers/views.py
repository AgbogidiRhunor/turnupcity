from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.text import slugify
from .models import OrganizerProfile, StaffRequest, StaffMembership
from .forms import OrganizerProfileForm, StaffRequestForm
from events.models import Event


def organizer_public_profile(request, slug):
    organizer = get_object_or_404(OrganizerProfile, slug=slug)
    events = Event.objects.filter(organizer=organizer, status=Event.STATUS_PUBLISHED).order_by('-start_date')
    return render(request, 'organizers/public_profile.html', {
        'organizer': organizer,
        'events': events,
    })


@login_required
def organizer_dashboard(request):
    try:
        organizer = request.user.organizer_profile
    except OrganizerProfile.DoesNotExist:
        messages.info(request, 'Please set up your organizer profile first.')
        return redirect('organizers:setup')

    events = Event.objects.filter(organizer=organizer).order_by('-created_at')
    pending_staff = StaffRequest.objects.filter(organizer=organizer, status=StaffRequest.STATUS_PENDING)
    staff_members = StaffMembership.objects.filter(organizer=organizer, is_active=True)

    from orders.models import Order
    from tickets.models import Ticket
    from django.db.models import Sum
    total_revenue = Order.objects.filter(
        event__organizer=organizer,
        status=Order.STATUS_PAID
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    total_tickets = Ticket.objects.filter(
        ticket_type__event__organizer=organizer,
        order__status=Order.STATUS_PAID
    ).count()

    from refunds.models import RefundRequest
    pending_refund_count = RefundRequest.objects.filter(
        order__event__organizer=organizer,
        status=RefundRequest.STATUS_PENDING
    ).count()

    return render(request, 'organizers/dashboard.html', {
        'organizer': organizer,
        'events': events,
        'pending_staff': pending_staff,
        'staff_members': staff_members,
        'total_revenue': total_revenue,
        'total_tickets': total_tickets,
        'pending_staff_count': pending_staff.count(),
        'pending_refund_count': pending_refund_count,
    })


@login_required
def organizer_setup(request):
    if hasattr(request.user, 'organizer_profile'):
        return redirect('organizers:dashboard')

    if request.method == 'POST':
        form = OrganizerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            base_slug = slugify(profile.organization_name)
            slug = base_slug
            counter = 1
            while OrganizerProfile.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            profile.slug = slug
            profile.save()
            request.user.role = 'organizer'
            request.user.save()
            messages.success(request, 'Organizer profile created! Awaiting verification.')
            return redirect('organizers:dashboard')
    else:
        form = OrganizerProfileForm()

    return render(request, 'organizers/setup.html', {'form': form})


@login_required
def organizer_edit(request):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    if request.method == 'POST':
        form = OrganizerProfileForm(request.POST, request.FILES, instance=organizer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('organizers:dashboard')
    else:
        form = OrganizerProfileForm(instance=organizer)
    return render(request, 'organizers/edit.html', {'form': form, 'organizer': organizer})


@login_required
def staff_requests_list(request):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    requests = StaffRequest.objects.filter(organizer=organizer).order_by('-created_at')
    from refunds.models import RefundRequest
    pending_refund_count = RefundRequest.objects.filter(
        order__event__organizer=organizer, status=RefundRequest.STATUS_PENDING
    ).count()
    return render(request, 'organizers/staff_requests.html', {
        'organizer': organizer,
        'requests': requests,
        'pending_staff_count': StaffRequest.objects.filter(organizer=organizer, status=StaffRequest.STATUS_PENDING).count(),
        'pending_refund_count': pending_refund_count,
    })


@login_required
def approve_staff_request(request, pk):
    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    staff_req = get_object_or_404(StaffRequest, pk=pk, organizer=organizer)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            staff_req.status = StaffRequest.STATUS_APPROVED
            staff_req.reviewed_at = timezone.now()
            staff_req.save()
            StaffMembership.objects.get_or_create(user=staff_req.user, organizer=organizer)
            messages.success(request, f'{staff_req.user.display_name} has been approved as staff.')
        elif action == 'reject':
            staff_req.status = StaffRequest.STATUS_REJECTED
            staff_req.reviewed_at = timezone.now()
            staff_req.save()
            messages.info(request, f'Request from {staff_req.user.display_name} rejected.')
    return redirect('organizers:staff_requests')


@login_required
def request_to_work(request, slug):
    organizer = get_object_or_404(OrganizerProfile, slug=slug)
    if organizer.user == request.user:
        messages.error(request, "You can't request to work for yourself.")
        return redirect('organizers:public_profile', slug=slug)

    existing = StaffRequest.objects.filter(user=request.user, organizer=organizer).first()
    if existing:
        messages.info(request, f'You already have a {existing.get_status_display()} request for this organizer.')
        return redirect('organizers:public_profile', slug=slug)

    if request.method == 'POST':
        form = StaffRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.organizer = organizer
            req.save()
            messages.success(request, 'Staff request submitted!')
            return redirect('organizers:public_profile', slug=slug)
    else:
        form = StaffRequestForm()

    return render(request, 'organizers/request_to_work.html', {'organizer': organizer, 'form': form})

@login_required
def withdrawal_dashboard(request):
    """Main withdrawal page - balance, bank account, history."""
    organizer = get_object_or_404(OrganizerProfile, user=request.user)

    from django.db.models import Sum
    from orders.models import Order
    from .models import WithdrawalRequest

    total_earned = Order.objects.filter(
        event__organizer=organizer, status=Order.STATUS_PAID
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    total_withdrawn = WithdrawalRequest.objects.filter(
        organizer=organizer, status=WithdrawalRequest.STATUS_COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_pending = WithdrawalRequest.objects.filter(
        organizer=organizer,
        status__in=[WithdrawalRequest.STATUS_PENDING, WithdrawalRequest.STATUS_PROCESSING]
    ).aggregate(total=Sum('amount'))['total'] or 0

    available_balance = total_earned - total_withdrawn - total_pending
    bank_account = getattr(organizer, 'bank_account', None)
    withdrawals = WithdrawalRequest.objects.filter(organizer=organizer)

    from refunds.models import RefundRequest
    return render(request, 'organizers/withdrawal_dashboard.html', {
        'organizer': organizer,
        'total_earned': total_earned,
        'total_withdrawn': total_withdrawn,
        'total_pending': total_pending,
        'available_balance': available_balance,
        'bank_account': bank_account,
        'withdrawals': withdrawals,
        'pending_refund_count': RefundRequest.objects.filter(
            order__event__organizer=organizer, status=RefundRequest.STATUS_PENDING
        ).count(),
        'pending_staff_count': StaffRequest.objects.filter(
            organizer=organizer, status=StaffRequest.STATUS_PENDING
        ).count(),
    })


@login_required
def setup_bank_account(request):
    """Add or update bank account for withdrawals."""
    organizer = get_object_or_404(OrganizerProfile, user=request.user)

    if request.method == 'POST':
        account_number = request.POST.get('account_number', '').strip()
        bank_code = request.POST.get('bank_code', '').strip()
        bank_name = request.POST.get('bank_name', '').strip()

        if not account_number or not bank_code:
            messages.error(request, 'Please provide both account number and bank.')
            return redirect('organizers:withdrawal_dashboard')

        from orders.paystack import resolve_account, create_transfer_recipient
        verify_resp = resolve_account(account_number, bank_code)

        if not verify_resp.get('status'):
            messages.error(request, f"Could not verify account: {verify_resp.get('message', 'Invalid account details.')}")
            return redirect('organizers:withdrawal_dashboard')

        account_name = verify_resp['data']['account_name']
        recipient_resp = create_transfer_recipient(account_name, account_number, bank_code)

        if not recipient_resp.get('status'):
            messages.error(request, f"Could not register account: {recipient_resp.get('message', 'Try again.')}")
            return redirect('organizers:withdrawal_dashboard')

        recipient_code = recipient_resp['data']['recipient_code']
        from .models import BankAccount
        BankAccount.objects.update_or_create(
            organizer=organizer,
            defaults={
                'bank_name': bank_name,
                'bank_code': bank_code,
                'account_number': account_number,
                'account_name': account_name,
                'paystack_recipient_code': recipient_code,
                'is_verified': True,
            }
        )
        messages.success(request, f'Bank account verified and saved: {account_name}')
        return redirect('organizers:withdrawal_dashboard')

    from orders.paystack import get_banks
    banks_resp = get_banks()
    banks = banks_resp.get('data', []) if banks_resp.get('status') else []
    from refunds.models import RefundRequest
    return render(request, 'organizers/setup_bank_account.html', {
        'organizer': organizer,
        'banks': banks,
        'bank_account': getattr(organizer, 'bank_account', None),
        'pending_refund_count': RefundRequest.objects.filter(
            order__event__organizer=organizer, status=RefundRequest.STATUS_PENDING
        ).count(),
        'pending_staff_count': StaffRequest.objects.filter(
            organizer=organizer, status=StaffRequest.STATUS_PENDING
        ).count(),
    })


@login_required
def request_withdrawal(request):
    """Submit and immediately process a withdrawal via Paystack Transfer."""
    if request.method != 'POST':
        return redirect('organizers:withdrawal_dashboard')

    organizer = get_object_or_404(OrganizerProfile, user=request.user)
    bank_account = getattr(organizer, 'bank_account', None)

    if not bank_account or not bank_account.is_verified:
        messages.error(request, 'Please set up a verified bank account first.')
        return redirect('organizers:withdrawal_dashboard')

    try:
        amount = float(request.POST.get('amount', 0))
    except (ValueError, TypeError):
        messages.error(request, 'Invalid amount entered.')
        return redirect('organizers:withdrawal_dashboard')

    if amount < 100:
        messages.error(request, 'Minimum withdrawal amount is ₦100.')
        return redirect('organizers:withdrawal_dashboard')

    from django.db.models import Sum
    from orders.models import Order
    from .models import WithdrawalRequest

    total_earned = Order.objects.filter(
        event__organizer=organizer, status=Order.STATUS_PAID
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    total_withdrawn = WithdrawalRequest.objects.filter(
        organizer=organizer, status=WithdrawalRequest.STATUS_COMPLETED
    ).aggregate(total=Sum('amount'))['total'] or 0
    total_pending = WithdrawalRequest.objects.filter(
        organizer=organizer,
        status__in=[WithdrawalRequest.STATUS_PENDING, WithdrawalRequest.STATUS_PROCESSING]
    ).aggregate(total=Sum('amount'))['total'] or 0
    available = float(total_earned - total_withdrawn - total_pending)

    if amount > available:
        messages.error(request, f'Insufficient balance. Available: ₦{available:,.2f}')
        return redirect('organizers:withdrawal_dashboard')

    import uuid as _uuid
    reference = f"WD-{_uuid.uuid4().hex[:12].upper()}"
    withdrawal = WithdrawalRequest.objects.create(
        organizer=organizer,
        amount=amount,
        paystack_reference=reference,
        status=WithdrawalRequest.STATUS_PROCESSING,
    )

    from orders.paystack import initiate_transfer
    transfer_resp = initiate_transfer(
        amount_naira=amount,
        recipient_code=bank_account.paystack_recipient_code,
        reference=reference,
        reason=f'TurnUpCity withdrawal for {organizer.organization_name}',
    )

    if transfer_resp.get('status'):
        transfer_data = transfer_resp.get('data', {})
        withdrawal.paystack_transfer_code = transfer_data.get('transfer_code', '')
        withdrawal.status = WithdrawalRequest.STATUS_PROCESSING
        withdrawal.save()
        messages.success(request, f'Withdrawal of ₦{amount:,.2f} initiated! It will arrive in your account within minutes.')
    else:
        withdrawal.status = WithdrawalRequest.STATUS_FAILED
        withdrawal.failure_reason = transfer_resp.get('message', 'Unknown error from Paystack.')
        withdrawal.save()
        messages.error(request, f'Withdrawal failed: {withdrawal.failure_reason}')

    return redirect('organizers:withdrawal_dashboard')
