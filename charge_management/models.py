from django.db import models
from django.contrib.auth.models import User

# فروشنده
class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.user.username

# تراکنش اعتبار
class CreditTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('INCREASE', 'Increase'),
        ('DECREASE', 'Decrease'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vendor} - {self.transaction_type} - {self.amount}"


class CreditRequest(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    credit_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request by {self.vendor} for {self.credit_amount}"
