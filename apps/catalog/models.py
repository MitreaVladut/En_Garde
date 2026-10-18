from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})

    def get_primary_image(self):
        image = self.images.order_by('position', 'id').first()
        return image.file.url if image and image.file else None

    @property
    def min_price(self):
        min_p = self.variants.aggregate(min_p=models.Min('price'))['min_p']
        return min_p if min_p is not None else Decimal('0.00')

    @property
    def is_in_stock(self):
        return any(v.get_available_stock() > 0 for v in self.variants.all())

    @property
    def total_available_stock(self):
        return sum(v.get_available_stock() for v in self.variants.all())


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=50, unique=True)
    size = models.CharField(max_length=50, blank=True, default='')
    handedness = models.CharField(max_length=50, blank=True, default='')
    grip_type = models.CharField(max_length=50, blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Variant'
        verbose_name_plural = 'Variants'
        ordering = ['id']

    def __str__(self):
        parts = [self.product.name]
        descriptors = []
        if self.size:
            descriptors.append(f"Size: {self.size}")
        if self.handedness:
            descriptors.append(f"Hand: {self.handedness}")
        if self.grip_type:
            descriptors.append(f"Grip: {self.grip_type}")
        if descriptors:
            return f"{self.product.name} ({', '.join(descriptors)})"
        return f"{self.product.name} (SKU: {self.sku})"

    @property
    def label(self):
        descriptors = []
        if self.size:
            descriptors.append(f"Size {self.size}")
        if self.handedness:
            descriptors.append(f"{self.handedness} Hand")
        if self.grip_type:
            descriptors.append(f"{self.grip_type} Grip")
        return ", ".join(descriptors) if descriptors else "Standard"

    def get_available_stock(self):
        try:
            from apps.orders.models import StockReservation
            from django.utils import timezone
            reserved = StockReservation.objects.filter(
                variant=self,
                state='active',
                expires_at__gt=timezone.now()
            ).aggregate(total=models.Sum('quantity'))['total'] or 0
            return max(0, self.stock - reserved)
        except Exception:
            return self.stock


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    file = models.ImageField(upload_to='products/', blank=True, null=True)
    position = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['position', 'id']

    def __str__(self):
        return f"Image for {self.product.name} (#{self.position})"


class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField(max_length=100)   # e.g. 'weapon_type', 'certification', 'level'
    value = models.CharField(max_length=100)  # e.g. 'foil', '800N FIE', 'Competition'

    class Meta:
        verbose_name = 'Product Attribute'
        verbose_name_plural = 'Product Attributes'
        indexes = [
            models.Index(fields=['name', 'value']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Wishlist Item'
        verbose_name_plural = 'Wishlist Items'
        unique_together = ('user', 'variant')

    def __str__(self):
        return f"{self.user.email} - {self.variant}"
