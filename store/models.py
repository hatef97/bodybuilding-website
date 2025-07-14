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



class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    phone_number = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    
    def __str__(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'
    
    @property
    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'
    
    class Meta:
        permissions = [
            ('send_private_email', 'Can send private email to user by the button'),
        ]



# Order model: Represents a completed order for a user
class Order(models.Model):
    ORDER_STATUS_PAID = 'p'
    ORDER_STATUS_UNPAID = 'u'
    ORDER_STATUS_CANCELED = 'c'
    ORDER_STATUS = [
        (ORDER_STATUS_PAID,'Paid'),
        (ORDER_STATUS_UNPAID,'Unpaid'),
        (ORDER_STATUS_CANCELED,'Canceled'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    datetime_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=ORDER_STATUS, default=ORDER_STATUS_UNPAID)



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
        