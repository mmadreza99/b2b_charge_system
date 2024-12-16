from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CreditRequest, Vendor
from .serializers import CreditRequestSerializer


class CreditRequestAPIView(APIView):
    def post(self, request):
        serializer = CreditRequestSerializer(data=request.data)
        if serializer.is_valid():
            vendor = serializer.validated_data['vendor']
            amount = serializer.validated_data['credit_amount']

            # اعتبارسنجی و ذخیره درخواست
            if amount > 0:
                serializer.save(status='PENDING')
                return Response({"message": "Credit request submitted successfully."}, status=status.HTTP_201_CREATED)
            return Response({"error": "Invalid credit amount."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
