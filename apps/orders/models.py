from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.catalog.models import Variant


class DeliveryMethod(models.Model):
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=8, decimal_places=2)
    estimated_days = models.CharField(max_length=50)  # e.g., "3-5 days"

    class Meta:
        verbose_name = 'Delivery Method'
        verbose_name_plural = 'Delivery Methods'

    def __str__(self):
        return f"{self.name} - €{self.cost} ({self.estimated_days})"


class DiscountCode(models.Model):
    TYPE_CHOICES = (
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (€)'),
    )
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    value = models.DecimalField(max_digits=8, decimal_places=2)
    expires_at = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=100)
    used_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Discount Code'
        verbose_name_plural = 'Discount Codes'

    def __str__(self):
        return f"{self.code} ({self.get_type_display()} {self.value})"

    @property
    def is_valid(self):
        return self.expires_at > timezone.now() and self.used_count < self.max_uses

    def calculate_discount(self, subtotal):
        if not self.is_valid:
            return Decimal('0.00')
        if self.type == 'percentage':
            return (subtotal * (self.value / Decimal('100.00'))).quantize(Decimal('0.01'))
        elif self.type == 'fixed':
            return min(subtotal, self.value)
        return Decimal('0.00')


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'New', 'New'
        PAID = 'Paid', 'Paid'
        SHIPPED = 'Shipped', 'Shipped'
        DELIVERED = 'Delivered', 'Delivered'
        CANCELLED = 'Cancelled', 'Cancelled'

    ALLOWED_TRANSITIONS = {
        Status.NEW: [Status.PAID, Status.CANCELLED],
        Status.PAID: [Status.SHIPPED, Status.CANCELLED],
        Status.SHIPPED: [Status.DELIVERED],
        Status.DELIVERED: [],
        Status.CANCELLED: [],
    }

    number = models.CharField(max_length=32, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    delivery_method = models.ForeignKey(DeliveryMethod, on_delete=models.PROTECT, related_name='orders')
    discount_code = models.ForeignKey(DiscountCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_session_id = models.CharField(max_length=255, blank=True, default='')

    # Address snapshot
    shipping_full_name = models.CharField(max_length=150)
    shipping_street = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='Romania')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.number} ({self.status}) - €{self.total}"

    def can_transition_to(self, new_status):
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])

    @property
    def allowed_next_statuses(self):
        # Staff transitions (Paid is only through webhook)
        allowed = self.ALLOWED_TRANSITIONS.get(self.status, [])
        return [s for s in allowed if s != self.Status.PAID]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    product_name = models.CharField(max_length=200)
    variant_label = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'

    def __str__(self):
        return f"{self.quantity}x {self.product_name} - {self.variant_label}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class StockReservation(models.Model):
    STATE_CHOICES = (
        ('active', 'Active'),
        ('used', 'Used'),
        ('released', 'Released'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='reservations')
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='reservations')
    quantity = models.PositiveIntegerField()
    expires_at = models.DateTimeField()
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='active')

    class Meta:
        verbose_name = 'Stock Reservation'
        verbose_name_plural = 'Stock Reservations'
        indexes = [
            models.Index(fields=['variant', 'state', 'expires_at']),
        ]

    def __str__(self):
        return f"Reservation #{self.id} for {self.variant.sku} ({self.quantity} pcs, {self.state})"
