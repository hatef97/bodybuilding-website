from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from .models import *



class StockFilter(admin.SimpleListFilter):
    LESS_THAN_3 = '<3'
    BETWEEN_3_and_10 = '3<=10'
    MORE_THAN_10 = '>10'
    title = 'Critical Stock Status'
    parameter_name = 'stock'

    def lookups(self, request, model_admin):
        return [
            (StockFilter.LESS_THAN_3, 'High'),
            (StockFilter.BETWEEN_3_and_10, 'Medium'),
            (StockFilter.MORE_THAN_10, 'OK'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == StockFilter.LESS_THAN_3:
            return queryset.filter(stock__lt=3)
        if self.value() == StockFilter.BETWEEN_3_and_10:
            return queryset.filter(stock__range=(3, 10))
        if self.value() == StockFilter.MORE_THAN_10:
            return queryset.filter(stock__gt=10)



@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'price', 'category', 'stock', 'image', 'created_at']
    list_per_page = 10
    list_editable = ['price']
    list_select_related = ['category']
    list_filter = ['created_at', StockFilter]
    actions = ['clear_stock']
    search_fields = ['name', ]


    def get_queryset(self, request):
        return super().get_queryset(request) \
                .prefetch_related('comments') \
                .annotate(
                    comments_count=Count('comments'),
                )

    def stock_status(self, product):
        if product.stock < 10:
            return 'Low'
        if product.stock > 50:
            return 'High'
        return 'Medium'
    
    @admin.display(description='# comments', ordering='comments_count')
    def num_of_comments(self, product):
        url = (
            reverse('admin:store_comment_changelist') 
            + '?'
            + urlencode({
                'product__id': product.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, product.comments_count)
        
    
    @admin.display(ordering='category__name')
    def product_category(self, product):
        return product.category.name

    
    @admin.action(description='Clear inventory')
    def clear_inventory(self, request, queryset):
        update_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f'{update_count} of products inventories cleared to zero.',
            messages.ERROR,
        )



# Inline admin for CartItem to embed in Cart
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0  # Do not show extra empty forms
    readonly_fields = ('product', 'quantity', 'total_price_display')
    can_delete = False
    verbose_name = 'Cart Item'
    verbose_name_plural = 'Cart Items'

    def total_price_display(self, obj):
        """Display computed total price for each cart item."""
        return obj.total_price()
    total_price_display.short_description = 'Total Price'



@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Cart model.
    Includes inline display of CartItems, price summaries, and filtering.
    """
    list_display = ('user', 'created_at', 'item_count', 'total_price_display')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'user__email')
    date_hierarchy = 'created_at'
    inlines = (CartItemInline,)
    readonly_fields = ('created_at', 'item_count', 'total_price_display')
    ordering = ('-created_at',)

    def item_count(self, obj):
        """Count of items in the cart."""
        return obj.cart_items.count()
    item_count.short_description = 'Items Count'

    def total_price_display(self, obj):
        """Total price for all items in the cart."""
        return obj.total_price()
    total_price_display.short_description = 'Total Price'



@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
   
    """
    Admin interface for the CartItem model.
    Allows direct management of cart items with computed total price.
    """
    list_display = ('cart', 'user', 'product', 'quantity', 'total_price_display')
    list_editable = ('quantity',)
    list_filter = ('product', 'cart__user')
    search_fields = (
        'product__name',
        'cart__user__username',
        'cart__user__email',
    )
    readonly_fields = ('total_price_display',)
    ordering = ('-cart__created_at',)

    def user(self, obj):
        """Retrieve the user associated with the cart."""
        return obj.cart.user
    user.short_description = 'User'
    user.admin_order_field = 'cart__user__username'

    def total_price_display(self, obj):
        """Display the computed total price for this cart item."""
        return obj.total_price()
    total_price_display.short_description = 'Total Price'
    total_price_display.admin_order_field = 'quantity'



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'shipping_address_short', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'created_at', 'user')
    search_fields = ('id', 'user__username', 'user__email', 'shipping_address')
    date_hierarchy = 'created_at'
    readonly_fields = ('total_price', 'created_at', 'cart_items_summary')
    ordering = ('-created_at',)
    fields = ('user', 'status', 'shipping_address', 'total_price', 'cart_items_summary', 'created_at')

    def shipping_address_short(self, obj):
        return (obj.shipping_address[:50] + '...') if len(obj.shipping_address) > 50 else obj.shipping_address
    shipping_address_short.short_description = 'Shipping Address'

    def cart_items_summary(self, obj):
        """Display a summary of cart items for this order."""
        items = obj.cart.cart_items.select_related('product')
        lines = [f"{item.product.name} (x{item.quantity}) - {item.total_price()}" for item in items]
        return format_html('<br>'.join(lines))
    cart_items_summary.short_description = 'Cart Items'



@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'payment_date', 'amount', 'status')
    list_editable = ('status',)
    list_filter = ('status', 'payment_date')
    search_fields = ('order__id', 'order__user__username', 'order__user__email')
    date_hierarchy = 'payment_date'
    readonly_fields = ('payment_date', 'order_details')
    actions = ('complete_payments', 'fail_payments')

    def user(self, obj):
        return obj.order.user.username
    user.short_description = 'User'
    user.admin_order_field = 'order__user__username'

    def order_details(self, obj):
        addr = obj.order.shipping_address
        short = (addr[:50] + '...') if len(addr) > 50 else addr
        return format_html('Order #{}: {}', obj.order.id, short)
    order_details.short_description = 'Order Details'

    def complete_payments(self, request, queryset):
        updated = 0
        for payment in queryset:
            if payment.status != 'completed':
                payment.complete_payment()
                updated += 1
        self.message_user(request, f"{updated} payment(s) marked as completed.")
    complete_payments.short_description = 'Mark selected payments as completed'

    def fail_payments(self, request, queryset):
        updated = 0
        for payment in queryset:
            if payment.status != 'failed':
                payment.fail_payment()
                updated += 1
        self.message_user(request, f"{updated} payment(s) marked as failed.")
    fail_payments.short_description = 'Mark selected payments as failed'
    