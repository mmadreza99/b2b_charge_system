from .models import Seller, CreditLog, Transaction
from .handlers import CreditTransactionHandler
from threading import Thread

from django.contrib.auth.models import User
from django.test import TestCase


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


class DoubleSpendingTestCase(TestCase):
    def setUp(self):
        # Create a User instance for the foreign key
        user = User.objects.create_user(username='testuser', password='testpass')

        # Create a seller with initial credentials
        self.seller = Seller.objects.create(user=user, credit=500.00)

    def test_double_spending(self):
        # Define two functions to increase validity simultaneously
        def add_credit1():
            print(CreditTransactionHandler.add_credit(seller_id=self.seller.id, amount=200))

        def add_credit2():
            print(CreditTransactionHandler.add_credit(seller_id=self.seller.id, amount=300))

        # Execute the function simultaneously in two threads
        t1 = Thread(target=add_credit1)
        t2 = Thread(target=add_credit2)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # We check the seller's credit.
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.credit, 1000.00)  # 500 + 200 + 300
