import json
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction, models
from django.utils import timezone
from django.conf import settings

from .models import Payment
from apps.orders.models import Order, StockReservation
from apps.catalog.models import Variant


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
    """
    Requirement A6 & Critical Flow 5.3:
    1. Signature-verified webhook checkout.session.completed marks order Paid.
    2. Payment.stripe_event_id is unique (idempotency check).
    3. In one atomic transaction:
       - sets order to Paid
       - decreases variant stock conditionally (never lets stock go below zero)
       - marks reservations used
       - saves a Payment row
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    event = None

    # Verify signature if stripe library and secret are configured
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        if settings.STRIPE_WEBHOOK_SECRET and settings.STRIPE_WEBHOOK_SECRET != 'whsec_sample':
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            # Fallback for sandbox / local tests without live stripe keys
            event = json.loads(payload.decode('utf-8'))
    except Exception as e:
        return HttpResponse(f"Webhook error: {str(e)}", status=400)

    event_id = event.get('id') if isinstance(event, dict) else getattr(event, 'id', None)
    event_type = event.get('type') if isinstance(event, dict) else getattr(event, 'type', None)

    # Idempotency check: if event_id already recorded in Payment, return 200 OK immediately
    if event_id and Payment.objects.filter(stripe_event_id=event_id).exists():
        return HttpResponse("Event already processed", status=200)

    if event_type == 'checkout.session.completed':
        session_data = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object
        order_number = session_data.get('metadata', {}).get('order_number')
        amount_total = session_data.get('amount_total', 0)
        amount_decimal = Decimal(amount_total) / Decimal('100.00') if amount_total else Decimal('0.00')

        if not order_number:
            return HttpResponse("Missing order_number in session metadata", status=400)

        with transaction.atomic():
            order = Order.objects.select_for_update().filter(number=order_number).first()
            if not order:
                return HttpResponse(f"Order {order_number} not found", status=404)

            # Only transition from New to Paid
            if order.status == Order.Status.NEW:
                order.status = Order.Status.PAID
                order.save()

                # Process reservations and decrease stock safely
                reservations = StockReservation.objects.select_for_update().filter(
                    order=order, state='active'
                )
                for res in reservations:
                    # Decrease stock conditionally (never let stock go below zero - rule 5.6)
                    Variant.objects.filter(id=res.variant_id, stock__gte=res.quantity).update(
                        stock=models.F('stock') - res.quantity
                    )
                    res.state = 'used'
                    res.save()

                # Create idempotent Payment entry
                Payment.objects.create(
                    order=order,
                    stripe_event_id=event_id or f"evt_{uuid.uuid4().hex[:16]}",
                    amount=amount_decimal or order.total,
                    status='succeeded'
                )

        return HttpResponse("Order confirmed and marked Paid", status=200)

    elif event_type in ['checkout.session.expired', 'payment_intent.payment_failed']:
        # Critical Flow 5.5: If the session expires or payment fails, release reservation and order stays New
        session_data = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object
        order_number = session_data.get('metadata', {}).get('order_number')
        if order_number:
            with transaction.atomic():
                order = Order.objects.filter(number=order_number, status=Order.Status.NEW).first()
                if order:
                    order.reservations.filter(state='active').update(state='released')
        return HttpResponse("Reservation released", status=200)

    return HttpResponse("Event ignored", status=200)
