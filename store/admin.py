from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from . import models



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



@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', ]
    list_per_page = 10
    ordering = ['user__last_name', 'user__first_name', ]
    search_fields = ['user__first_name__istartswith', 'user__last_name__istartswith', ]

    def first_name(self, customer):
        return customer.user.first_name
    
    def last_name(self, customer):
        return customer.user.last_name

    def email(self, customer):
        return customer.user.email



@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'status', ]
    list_editable = ['status']
    list_per_page = 10
    autocomplete_fields = ['product', ]   



class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    fields = ['product', 'quantity', 'price']
    extra = 0
    min_num = 1
    readonly_fields = ['price']



@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    autocomplete_fields = ['product', ]



@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'datetime_created', 'num_of_items']
    list_editable = ['status']
    list_per_page = 10
    ordering = ['-datetime_created']
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        return super() \
                .get_queryset(request) \
                .prefetch_related('items') \
                .annotate(
                    items_count=Count('items')
                )

    @admin.display(ordering='items_count', description='# items')
    def num_of_items(self, order):
        return order.items_count



# Inline admin for CartItem to embed in Cart
class CartItemInline(admin.TabularInline):
    model = models.CartItem
    fields = ['id', 'product', 'quantity']
    extra = 0
    min_num = 1



@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at']
    inlines = [CartItemInline]



@admin.register(models.Payment)
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



@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display     = ['name', 'description_excerpt', 'num_of_products']
    search_fields    = ['name', 'description']
    ordering         = ['name']
    list_per_page    = 10
    actions          = ['clear_descriptions']

    def get_queryset(self, request):
        # Annotate each Category with the count of related Products (reverse relation is 'products')
        return super().get_queryset(request) \
                       .annotate(product_count=Count('products'))

    @admin.display(ordering='product_count', description='# Products')
    def num_of_products(self, category):
        # Link into the Product changelist filtered by this category
        url = (
            reverse('admin:store_product_changelist')  # adjust 'store' to your app_label
            + '?'
            + urlencode({'category__id__exact': category.id})
        )
        return format_html('<a href="{}">{}</a>', url, category.product_count)

    @admin.display(description='Description')
    def description_excerpt(self, category):
        if not category.description:
            return format_html('<span style="color: #777;">—</span>')
        text = category.description
        return text if len(text) <= 75 else f'{text[:75]}…'

    @admin.action(description='Clear descriptions for selected categories')
    def clear_descriptions(self, request, queryset):
        updated = queryset.update(description='')
        self.message_user(
            request,
            f'Description cleared on {updated} category(ies).',
            messages.SUCCESS,
        )
        