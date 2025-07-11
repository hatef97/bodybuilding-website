from django.contrib import admin
from django.utils.html import format_html

from .models import Product



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface definition for the Product model.
    Provides list display, filters, search, and custom actions for stock management.
    """
    # Columns to display in the list view
    list_display = (
        'name',
        'price',
        'stock',
        'is_in_stock',
        'created_at',
        'image_thumbnail',
    )
    # Allow inline editing of stock and price directly from the list view
    list_editable = ('price', 'stock')
    # Filters in the sidebar
    list_filter = (
        'created_at',
        'stock',
    )
    # Enable search on name and description fields
    search_fields = ('name', 'description')
    # Make certain fields read-only in the form view
    readonly_fields = ('created_at', 'image_thumbnail')
    # Add a date-based drill-down navigation by creation date
    date_hierarchy = 'created_at'
    # Custom actions available for bulk operations
    actions = ('mark_out_of_stock', 'restock_selected')

    def is_in_stock(self, obj):
        """Display a boolean icon for stock availability."""
        return obj.is_in_stock()
    is_in_stock.boolean = True
    is_in_stock.short_description = 'In Stock'

    def image_thumbnail(self, obj):
        """Render a small thumbnail of the product image, if available."""
        if obj.image:
            return format_html(
                '<img src="{}" style="height:50px; border-radius:4px;"/>',
                obj.image.url
            )
        return format_html('<span style="color:#999;">No image</span>')
    image_thumbnail.short_description = 'Image Preview'

    def mark_out_of_stock(self, request, queryset):
        """Custom action to set stock to zero for selected products."""
        updated = queryset.update(stock=0)
        self.message_user(request, f"{updated} product(s) marked as out of stock.")
    mark_out_of_stock.short_description = 'Mark selected products as out of stock'

    def restock_selected(self, request, queryset):
        """Custom action to restore stock to a default level for selected products."""
        default_amount = 10
        for product in queryset:
            product.stock += default_amount
            product.save()
        self.message_user(request, f"Restocked {queryset.count()} product(s) by {default_amount} units each.")
    restock_selected.short_description = 'Restock selected products by 10 units'
