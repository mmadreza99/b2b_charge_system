from rest_framework import serializers
from .models import Seller, CreditRequest, Transaction, CreditLog, PhoneNumber


# Serializer for Seller model
class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['id', 'name', 'email', 'phone_number', 'credit', 'created_at', 'updated_at']


# Serializer for CreditRequest model
class CreditRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRequest
        fields = ['id', 'seller', 'amount', 'is_approved', 'approved_by', 'created_at', 'approved_at']
        read_only_fields = ['id', 'is_approved', 'approved_by', 'approved_at', 'seller']


# Serializer for Transaction model
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'seller', 'phone_number', 'amount', 'created_at']
        read_only_fields = ['seller', 'created_at']

    def validate_phone_number(self, value):
        """
        Custom validation for phone_number field.
        """
        # Check if the phone number exists in the ValidPhoneNumber table and is active
        if not PhoneNumber.is_valid_phone_number(value):
            raise serializers.ValidationError("The provided phone number is not registered or is inactive.")
        return value

    def validate_amount(self, value):
        """
        Validate that seller has sufficient credit
        """
        seller = self.context['request'].user.seller
        if seller.credit < value:
            raise serializers.ValidationError("Insufficient credit for this transaction.")
        return value

    def validate(self, data):
        data['seller'] = self.context['request'].user.seller
        return data


# Serializer for CreditLog model
class CreditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditLog
        fields = ['id', 'seller', 'balance_snapshot', 'amount', 'description', 'created_at']
