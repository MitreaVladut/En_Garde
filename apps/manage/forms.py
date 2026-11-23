from django import forms
from django.utils.text import slugify
from apps.catalog.models import Product, Variant, Category, ProductImage


class ProductForm(forms.ModelForm):
    image = forms.ImageField(required=False, label='Primary Product Image', widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. FIE Maraging Electric Foil'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Technical details, materials, and safety certifications...'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        product = super().save(commit=False)
        if not product.slug:
            base_slug = slugify(product.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=product.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            product.slug = slug
        if commit:
            product.save()
            image_file = self.cleaned_data.get('image')
            if image_file:
                ProductImage.objects.create(product=product, file=image_file, position=0)
        return product


class VariantForm(forms.ModelForm):
    class Meta:
        model = Variant
        fields = ['sku', 'size', 'handedness', 'grip_type', 'price', 'stock']
        widgets = {
            'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. FOIL-FIE-P-R5'}),
            'size': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 5, 52, M, 2.0m'}),
            'handedness': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Right, Left, or Ambidextrous'}),
            'grip_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Visconti, French, Belgian'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def save(self, commit=True):
        category = super().save(commit=False)
        if not category.slug:
            base_slug = slugify(category.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=category.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            category.slug = slug
        if commit:
            category.save()
        return category
