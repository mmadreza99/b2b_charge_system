from django.utils import timezone

from django.db import models, transaction
from django.contrib.auth.models import User  # To associate admin users approving credits


# Seller model to manage sellers and their credit
class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # Seller's name
    email = models.EmailField(unique=True)  # Unique email for the seller
    phone_number = models.CharField(max_length=15, unique=True)  # Unique phone number
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Seller's available credit
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when seller was created
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp for the last update

    def __str__(self):
        return self.name  # String representation for Seller


# Model to log credit requests and approvals
class CreditRequest(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE,
                               related_name='credit_requests')  # Seller requesting credit
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Requested credit amount
    is_approved = models.BooleanField(default=False)  # Approval status
    approved_by = models.ForeignKey(User, null=True, blank=True,
                                    on_delete=models.SET_NULL)  # Admin approving the credit
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when request was created
    approved_at = models.DateTimeField(null=True, blank=True)  # Timestamp when request was approved

    def __str__(self):
        return f"{self.seller.name} - {self.amount}"

    def approve(self, user):
        from charge_management.handlers import CreditTransactionHandler

        with transaction.atomic():
            # Approve the request and update seller's credit
            self.is_approved = True
            self.approved_by = user
            self.approved_at = timezone.now()

            # Update seller's credit
            result = CreditTransactionHandler.add_credit(seller_id=self.seller.id,
                                                         amount=self.amount)
            if result['success']:
                self.save()


# Model to log transactions for recharge operations
class Transaction(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE,
                               related_name='transactions')  # Seller performing the transaction
    phone_number = models.CharField(max_length=15)  # Phone number to recharge
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Amount of recharge
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of the transaction

    def __str__(self):
        return f"Transaction by {self.seller.name} to {self.phone_number} - {self.amount}"

    # Ensures credit deduction logic is handled correctly
    def save(self, *args, **kwargs):
        if self.seller.credit < self.amount:
            raise ValueError("Insufficient credit for this transaction.")
        super().save(*args, **kwargs)
        # Deduct the credit after transaction is saved
        self.seller.credit -= self.amount
        self.seller.save()


# Model to log changes in seller's credit (credit history)
class CreditLog(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE,
                               related_name='credit_logs')  # Seller associated with the log
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Change in credit (positive or negative)
    balance_snapshot = models.DecimalField(max_digits=10, decimal_places=2)  # Seller's inventory after change
    description = models.CharField(max_length=255)  # Description of the change
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when log was created

    def __str__(self):
        return f"Log for {self.seller.name}: {self.amount} - {self.description}"


class PhoneNumber(models.Model):
    phone_number = models.CharField(max_length=15, unique=True, verbose_name="Phone Number")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="Added At")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    def __str__(self):
        return self.phone_number

    class Meta:
        verbose_name = "Valid Phone Number"
        verbose_name_plural = "Valid Phone Numbers"
        ordering = ['-added_at']

    @staticmethod
    def is_valid_phone_number(phone_number):
        return PhoneNumber.objects.filter(phone_number=phone_number, is_active=True).exists()
