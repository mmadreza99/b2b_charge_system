from django.db import transaction
from django.http import Http404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .handlers import CreditTransactionHandler
from .models import Seller, CreditRequest, Transaction, CreditLog
from .serializers import SellerSerializer, CreditRequestSerializer, TransactionSerializer, CreditLogSerializer


class CreditBalanceView(APIView):
    """
    Return the current credit balance of the authenticated user.
    """
    authentication_classes = [JWTAuthentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def get(self, request):
        try:
            user = request.user
            seller = Seller.objects.get(user=user)  # Assuming Seller is tied to User
        except Seller.DoesNotExist:
            return Response(
                {"error": "The Seller associated with this user was not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response({
            "seller_name": seller.name,
            "current_balance": seller.credit
        })


# View to list and create Sellers
class SellerListCreateView(generics.ListCreateAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer

    authentication_classes = [JWTAuthentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAdminUser]  # Ensure user is IsAdminUser


# View to retrieve, update, or delete a Seller
class SellerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer

    authentication_classes = [JWTAuthentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAdminUser]  # Ensure user is IsAdminUser


# View to handle Credit Requests
class CreditRequestCreateView(generics.CreateAPIView):
    queryset = CreditRequest.objects.all()
    serializer_class = CreditRequestSerializer

    authentication_classes = [JWTAuthentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    # Handle custom logic to approve the credit request
    def perform_create(self, serializer):
        serializer.validated_data['seller'] = self.request.user.seller
        serializer.save()  # Save credit request as pending


# View to approve a Credit Request
class CreditRequestApprovalView(APIView):
    authentication_classes = [JWTAuthentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAdminUser]  # Ensure user is IsAdminUser

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

                # Update seller's credit
                result = CreditTransactionHandler.add_credit(seller_id=credit_request.seller.id,
                                                             amount=credit_request.amount)

        except Exception as e:
            result = {"success": False, "message": f"An error occurred: {e}"}

        if result['success']:
            credit_request.save()
            return Response({"detail": "Credit request approved successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": result['message']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# View to handle recharge transactions
class TransactionCreateView(generics.CreateAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    authentication_classes = [JWTAuthentication]  # Enforce OAuth2 authentication
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
class CreditLogsListView(generics.ListAPIView):
    serializer_class = CreditLogSerializer

    authentication_classes = [JWTAuthentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAdminUser]  # Ensure user is authenticated

    def get_queryset(self):
        seller_id = self.kwargs['seller_id']
        return CreditLog.objects.filter(seller_id=seller_id)


# View to list credit logs for a seller
class CreditLogListView(generics.ListAPIView):
    serializer_class = CreditLogSerializer

    authentication_classes = [JWTAuthentication]  # Enforce OAuth2 authentication
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def get_queryset(self):
        try:
            seller = self.request.user.seller
        except Seller.DoesNotExist:
            raise Http404('The Seller associated with this user was not found.')
        return CreditLog.objects.filter(seller=seller)
