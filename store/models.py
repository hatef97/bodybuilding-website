from django.db import models
from django.conf import settings
from django.utils import timezone



# Product model: Represents an item available for purchase
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price with 2 decimal points
    stock = models.IntegerField()  # Track how many units are in stock
    image = models.ImageField(upload_to="products/", null=True, blank=True)  # Optional image
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set the timestamp when the product is created

    def __str__(self):
        return self.name

    def is_in_stock(self):
        """Check if the product is in stock."""
        return self.stock > 0

    def decrease_stock(self, quantity):
        """Decrease the stock after an order."""
        if quantity <= self.stock:
            self.stock -= quantity
            self.save()
            return True
        return False

    def increase_stock(self, quantity):
        """Increase the stock if needed."""
        self.stock += quantity
        self.save()
        