from django.test import TestCase
from .models import Seller, CreditLog
from .handlers import CreditTransactionHandler
from threading import Thread


class CreditTransactionTestCase(TestCase):
    def test_credit_increase(self):
        seller = Seller.objects.create(user_id=1, credit=500.00)
        CreditLog.objects.create(
            seller=seller,
            amount=-500.00,
            balance_snapshot=seller.credit,
            description=f"test_credit_increase"
        )
        seller.refresh_from_db()
        self.assertEqual(seller.credit, 700.00)


class DoubleSpendingTestCase(TestCase):
    def setUp(self):
        # ایجاد یک فروشنده با اعتبار اولیه
        self.seller = Seller.objects.create(user_id=1, credit=500.00)

    def test_double_spending(self):
        # تعریف دو تابع برای افزایش همزمان اعتبار
        def add_credit1():
            CreditTransactionHandler.add_credit(vendor_id=self.seller.id, amount=200.00)

        def add_credit2():
            CreditTransactionHandler.add_credit(vendor_id=self.seller.id, amount=300.00)

        # اجرای توابع به‌طور همزمان در دو Thread
        t1 = Thread(target=add_credit1)
        t2 = Thread(target=add_credit2)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # اعتبار فروشنده را بررسی می‌کنیم
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.credit, 1000.00)  # 500 + 200 + 300
