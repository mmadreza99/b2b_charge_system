from .models import Seller, CreditLog, Transaction, CreditRequest
from threading import Thread
from django.db import models

from django.test import TestCase
from decimal import Decimal
from django.contrib.auth.models import User


class CreditTransactionTestCase(TestCase):
    def test_credit_increase(self):
        # Create a User instance for the foreign key
        user = User.objects.create_user(username='testuser', password='testpass')

        # Create a Seller instance with the user
        seller = Seller.objects.create(user=user, credit=500.00)

        # Create a Transaction
        increase_amount = 10
        Transaction.objects.create(seller=seller,
                                   phone_number='09121234567',
                                   amount=increase_amount)

        # Create a CreditLog
        CreditLog.objects.create(
            seller=seller,
            amount=-increase_amount,
            balance_snapshot=seller.credit,
            description=f"test_credit_increase"
        )

        # Refresh the Seller from the database to check updated credit
        seller.refresh_from_db()

        # Assert the updated credit
        self.assertEqual(seller.credit, 490)


class DoubleSpendingTest(TestCase):
    def setUp(self):
        self.seller = Seller.objects.create(
            user=User.objects.create_user(username="seller", password="pass"),
            name="Seller",
            email="seller@example.com",
            phone_number="1234567890",
            credit=Decimal("100.00")
        )

    def make_transaction(self, amount):
        try:
            Transaction.objects.create(
                seller=self.seller,
                phone_number="1234567890",
                amount=amount
            )
        except ValueError as e:
            return str(e)

    def test_double_spending(self):
        # Simulate two threads trying to perform transactions at the same time
        results = []

        def run_transaction(amount):
            result = self.make_transaction(amount)
            if result:
                results.append(result)

        thread1 = Thread(target=run_transaction, args=(Decimal("90.00"),))
        thread2 = Thread(target=run_transaction, args=(Decimal("90.00"),))

        # Start the threads
        thread1.start()
        thread2.start()

        # Join the threads
        thread1.join()
        thread2.join()

        # Refresh the seller from the database
        self.seller.refresh_from_db()

        # Validate the final credit and number of transactions
        total_transactions = self.seller.transactions.aggregate(total=models.Sum('amount'))['total'] or Decimal(0)
        self.assertLessEqual(total_transactions, Decimal("100.00"), "Double spending occurred")
        self.assertGreaterEqual(self.seller.credit, Decimal(0), "Seller credit is negative")

        # Check results for debugging
        print("Results from threads:", results)


class SellerTransactionTest(TestCase):
    def setUp(self):
        # Create two admin users to approve credit requests
        self.admin1 = User.objects.create_user(username="admin1", password="adminpass1")
        self.admin2 = User.objects.create_user(username="admin2", password="adminpass2")

        # Create two sellers
        self.seller1 = Seller.objects.create(
            user=User.objects.create_user(username="seller1", password="pass1"),
            name="Seller 1",
            email="seller1@example.com",
            phone_number="1234567890",
            credit=Decimal("0.00")
        )

        self.seller2 = Seller.objects.create(
            user=User.objects.create_user(username="seller2", password="pass2"),
            name="Seller 2",
            email="seller2@example.com",
            phone_number="0987654321",
            credit=Decimal("0.00")
        )

    def test_credit_and_transactions(self):
        # Simulate 10 credit requests and approvals for both sellers
        for i in range(10):
            for seller, admin in [(self.seller1, self.admin1), (self.seller2, self.admin2)]:
                credit_request = CreditRequest.objects.create(seller=seller, amount=Decimal("1000.00"))
                credit_request.approve(admin)

        # Check the updated credit for both sellers
        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()
        self.assertEqual(self.seller1.credit, Decimal("10000.00"))  # 10 requests of 1000 each
        self.assertEqual(self.seller2.credit, Decimal("10000.00"))

        # Simulate 1000 recharge transactions for each seller
        for _ in range(1000):
            for seller in [self.seller1, self.seller2]:
                Transaction.objects.create(
                    seller=seller,
                    phone_number="1234567890",
                    amount=Decimal("5.00")
                )

        # Check the final credit for both sellers
        self.seller1.refresh_from_db()
        self.seller2.refresh_from_db()
        self.assertEqual(self.seller1.credit, Decimal("5000.00"))  # 10000 - (1000 x 5)
        self.assertEqual(self.seller2.credit, Decimal("5000.00"))

        # Ensure all transactions are logged
        self.assertEqual(self.seller1.transactions.count(), 1000)
        self.assertEqual(self.seller2.transactions.count(), 1000)
