from django.db import models
from django.conf import settings



class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name



class Discount(models.Model):
    discount = models.FloatField()
    description = models.CharField(max_length=255)



# Product model: Represents an item available for purchase
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    discounts = models.ManyToManyField(Discount, blank=True)

    def __str__(self):
        return self.name



# Cart model: Represents a shopping cart for a user
class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through="CartItem")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.user}"

    def total_price(self):
        """Calculate the total price of items in the cart."""
        total = sum([item.total_price() for item in self.cart_items.all()])
        return total



# CartItem model: Represents an individual product in the cart with a quantity
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="cart_items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def total_price(self):
        """Calculate total price for this item (quantity * product price)."""
        return self.quantity * self.product.price



# Order model: Represents a completed order for a user
class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('shipped', 'Shipped'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cart = models.OneToOneField(Cart, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user}"

    def save(self, *args, **kwargs):
        # Set total price of the order based on the cart
        self.total_price = self.cart.total_price()
        super().save(*args, **kwargs)



# Payment model: Represents a payment made for an order
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Payment for Order #{self.order.id}"

    def complete_payment(self):
        """Method to mark the payment as completed."""
        self.status = 'completed'
        self.save()

    def fail_payment(self):
        """Method to mark the payment as failed."""
        self.status = 'failed'
        self.save()
        