"""
URL configuration for b2b_charge_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from charge_management.views import (
    SellerListCreateView, SellerDetailView, CreditRequestCreateView,
    CreditRequestApprovalView, TransactionCreateView, CreditLogListView,
    credit_balance_view
)

urlpatterns = [
    path('credit_balance/', credit_balance_view, name='credit_balance_view'),
    path('sellers/', SellerListCreateView.as_view(), name='seller-list-create'),
    path('sellers/<int:pk>/', SellerDetailView.as_view(), name='seller-detail'),
    path('credit-requests/', CreditRequestCreateView.as_view(), name='credit-request-create'),
    path('credit-requests/<int:pk>/approve/', CreditRequestApprovalView.as_view(), name='credit-request-approve'),
    path('transactions/', TransactionCreateView.as_view(), name='transaction-create'),
    path('sellers/<int:seller_id>/logs/', CreditLogListView.as_view(), name='credit-log-list'),
]
