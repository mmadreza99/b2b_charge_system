from django.db import transaction
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Seller, CreditRequest, Transaction, CreditLog
from .serializers import SellerSerializer, CreditRequestSerializer, TransactionSerializer, CreditLogSerializer

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.permissions import IsAuthenticated


@api_view(['GET'])
@authentication_classes([OAuth2Authentication])  # Enforce OAuth2 authentication
@permission_classes([IsAuthenticated])  # Ensure user is authenticated
def credit_balance_view(request):
    """
    Return the current credit balance of the authenticated user.
    """
    user = request.user
    seller = Seller.objects.get(user=user)  # Assuming Seller is tied to User
    return Response({
        "seller_name": seller.name,
        "current_balance": seller.credit
    })


# View to list and create Sellers
class SellerListCreateView(generics.ListCreateAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer

    authentication_classes = [OAuth2Authentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated


# View to retrieve, update, or delete a Seller
class SellerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer

    authentication_classes = [OAuth2Authentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated


# View to handle Credit Requests
class CreditRequestCreateView(generics.CreateAPIView):
    queryset = CreditRequest.objects.all()
    serializer_class = CreditRequestSerializer

    authentication_classes = [OAuth2Authentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    # Handle custom logic to approve the credit request
    def perform_create(self, serializer):
        serializer.validated_data['seller'] = self.request.user.seller
        serializer.save()  # Save credit request as pending


# View to approve a Credit Request
class CreditRequestApprovalView(APIView):
    authentication_classes = [OAuth2Authentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def post(self, request, pk):
        try:
            credit_request = CreditRequest.objects.get(pk=pk, is_approved=False)
        except CreditRequest.DoesNotExist:
            return Response({"detail": "Credit request not found or already approved."},
                            status=status.HTTP_404_NOT_FOUND)
        try:
            with transaction.atomic():
                # Approve the request and update seller's credit
                credit_request.is_approved = True
                credit_request.approved_by = request.user
                credit_request.approved_at = timezone.now()
                credit_request.save()

                # Update seller's credit
                seller = credit_request.seller
                seller.credit += credit_request.amount
                seller.save()

                # Log the credit update
                CreditLog.objects.create(
                    seller=seller,
                    amount=credit_request.amount,
                    balance_snapshot=seller.credit,
                    description="Credit added via approval."
                )
        except Exception as e:
            return Response({"detail": f"Error in Create Credit Request Approval.{e}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"detail": "Credit request approved successfully."}, status=status.HTTP_200_OK)


# View to handle recharge transactions
class TransactionCreateView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    authentication_classes = [OAuth2Authentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    # Override perform_create to deduct credit after successful transaction
    def perform_create(self, serializer):
        transaction = serializer.save()  # Save the transaction
        # Log the deduction in credit history
        CreditLog.objects.create(
            seller=transaction.seller,
            amount=-transaction.amount,
            balance_snapshot=transaction.seller.credit,
            description=f"Recharge transaction to {transaction.phone_number}"
        )


# View to list all credit logs for a specific seller
class CreditLogListView(generics.ListAPIView):
    serializer_class = CreditLogSerializer

    authentication_classes = [OAuth2Authentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def get_queryset(self):
        seller_id = self.kwargs['seller_id']
        return CreditLog.objects.filter(seller_id=seller_id)
