from rest_framework import serializers
from .models import CreditTransaction, CreditRequest, Vendor


class CreditRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditRequest
        fields = ['id', 'vendor', 'phone_number', 'credit_amount', 'status']


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'user', 'credit']
