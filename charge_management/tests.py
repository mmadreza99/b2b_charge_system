from django.test import TestCase
from .models import Vendor, CreditTransaction
from .handlers import CreditTransactionHandler
from threading import Thread


class CreditTransactionTestCase(TestCase):
    def test_credit_increase(self):
        vendor = Vendor.objects.create(user_id=1, credit=500.00)
        CreditTransaction.objects.create(vendor=vendor, transaction_type='INCREASE', amount=200.00)

        vendor.refresh_from_db()
        self.assertEqual(vendor.credit, 700.00)


class DoubleSpendingTestCase(TestCase):
    def setUp(self):
        # ایجاد یک فروشنده با اعتبار اولیه
        self.vendor = Vendor.objects.create(user_id=1, credit=500.00)

    def test_double_spending(self):
        # تعریف دو تابع برای افزایش همزمان اعتبار
        def add_credit1():
            CreditTransactionHandler.add_credit(vendor_id=self.vendor.id, amount=200.00)

        def add_credit2():
            CreditTransactionHandler.add_credit(vendor_id=self.vendor.id, amount=300.00)

        # اجرای توابع به‌طور همزمان در دو Thread
        t1 = Thread(target=add_credit1)
        t2 = Thread(target=add_credit2)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # اعتبار فروشنده را بررسی می‌کنیم
        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.credit, 1000.00)  # 500 + 200 + 300
