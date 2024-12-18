from django.contrib import admin
from .models import Seller, CreditRequest, Transaction, CreditLog, PhoneNumber


# Register Seller model
@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number', 'credit', 'created_at', 'updated_at']
    search_fields = ['name', 'email', 'phone_number']
    list_filter = ['created_at', 'updated_at']
    ordering = ['-created_at']


# Register CreditRequest model
@admin.register(CreditRequest)
class CreditRequestAdmin(admin.ModelAdmin):
    list_display = ['seller', 'amount', 'is_approved', 'approved_by', 'created_at']
    search_fields = ['seller__name', 'seller__email']
    list_filter = ['is_approved', 'created_at']
    ordering = ['-created_at']
    actions = ['approve_requests']

    # Custom admin action to approve requests
    def approve_requests(self, request, queryset):
        for credit_request in queryset.filter(is_approved=False):
            credit_request.approve()  # Call the approve method in the model
        self.message_user(request, "Selected requests have been approved successfully.")

    approve_requests.short_description = "Approve selected credit requests"


# Register Transaction model
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['seller', 'phone_number', 'amount', 'created_at']
    search_fields = ['seller__name', 'phone_number']
    list_filter = ['created_at']
    ordering = ['-created_at']


# Register CreditLog model
@admin.register(CreditLog)
class CreditLogAdmin(admin.ModelAdmin):
    list_display = ['seller', 'amount', 'balance_snapshot', 'description', 'created_at']
    search_fields = ['seller__name', 'description']
    list_filter = ['created_at']
    ordering = ['-created_at']


@admin.register(PhoneNumber)
class ValidPhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'is_active', 'added_at')
    list_filter = ('is_active',)
    search_fields = ('phone_number', 'description')
