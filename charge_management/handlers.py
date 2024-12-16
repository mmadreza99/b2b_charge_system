from django.db import transaction
from .models import Vendor, CreditTransaction


class CreditTransactionHandler:
    @staticmethod
    def add_credit(vendor_id, amount):
        try:
            with transaction.atomic():
                # قفل کردن ردیف فروشنده برای جلوگیری از رقابت همزمان
                vendor = Vendor.objects.select_for_update().get(id=vendor_id)

                # افزودن اعتبار به حساب فروشنده
                vendor.credit += amount
                vendor.save()

                # ثبت تراکنش افزایش اعتبار
                CreditTransaction.objects.create(
                    vendor=vendor,
                    transaction_type='INCREASE',
                    amount=amount
                )

                return {"success": True, "message": "Credit successfully added."}

        except Vendor.DoesNotExist:
            return {"success": False, "message": "Vendor does not exist."}
        except Exception as e:
            return {"success": False, "message": f"An error occurred: {e}"}
