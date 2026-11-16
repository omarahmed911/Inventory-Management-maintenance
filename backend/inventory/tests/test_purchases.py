from rest_framework import status
from decimal import Decimal
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Purchase, PurchaseItem, Product, Payment


class PurchasesBaselineTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_create_purchase_increases_stock_and_creates_payment(self):
        initial_stock = self.product.stock_quantity
        payload = {
            "supplier": self.supplier.id,
            "total_amount": "800.00",
            "paid_amount": "500.00",
            "payment_type": "Cash",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "20.00",
                    "price": "40.00"
                }
            ]
        }
        response = self.client.post("/api/purchases/create/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["purchase_no"].startswith("PUR-"))
        self.assertEqual(Decimal(str(response.data["due_amount"])), Decimal("300.00"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, initial_stock + Decimal("20.00"))

        payment = Payment.objects.filter(party=self.supplier, payment_type="Debit").last()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal("800.00"))

    def test_create_purchase_exceeds_max_stock(self):
        # max_stock is 500, current stock is 100. Adding 500 would exceed max 500.
        payload = {
            "supplier": self.supplier.id,
            "total_amount": "20000.00",
            "paid_amount": "20000.00",
            "payment_type": "Cash",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "500.00",
                    "price": "40.00"
                }
            ]
        }
        with self.assertRaises(ValueError):
            self.client.post("/api/purchases/create/", payload, format="json")

    def test_get_purchases_and_single_purchase(self):
        payload = {
            "supplier": self.supplier.id,
            "total_amount": "400.00",
            "paid_amount": "400.00",
            "payment_type": "Cash",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "10.00",
                    "price": "40.00"
                }
            ]
        }
        res_create = self.client.post("/api/purchases/create/", payload, format="json")
        purchase_id = res_create.data["id"]

        res_list = self.client.get("/api/purchases/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res_list.data), 1)

        res_get = self.client.get(f"/api/purchases/{purchase_id}/")
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data["id"], purchase_id)
        self.assertEqual(len(res_get.data["items"]), 1)
