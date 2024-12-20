from django.db import transaction
from .models import Seller, CreditLog


class CreditTransactionHandler:
    @staticmethod
    def add_credit(seller_id, amount):
        try:
            with transaction.atomic():
                # Start a transaction and lock the seller row
                seller = Seller.objects.select_for_update().get(id=seller_id)

                # Update seller's credit
                seller.credit += amount
                seller.save()

                # Log the credit update
                CreditLog.objects.create(
                    seller=seller,
                    amount=amount,
                    balance_snapshot=seller.credit,
                    description=f"Credit added via approval."
                )

                return {"success": True, "message": "Credit successfully added."}

        except Seller.DoesNotExist:
            return {"success": False, "message": "Seller does not exist."}
        except Exception as e:
            return {"success": False, "message": f"An error occurred: {e}"}
