from rest_framework import status
from decimal import Decimal
from django.core.exceptions import ValidationError
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Sale, SaleItem, Product, Payment


class SalesBaselineTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_create_sale_reduces_stock_and_creates_payment(self):
        initial_stock = self.product.stock_quantity
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "10.00",
                    "per_item_price": "50.00"
                }
            ]
        }
        response = self.client.post("/api/sales/create/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["invoice_no"].startswith("INV"))

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, initial_stock - Decimal("10.00"))

        payment = Payment.objects.filter(party=self.customer, payment_type="Credit").last()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal("500.00"))

    def test_create_sale_insufficient_stock(self):
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "10000.00",
            "payment_mode": "Cash",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "999.00",
                    "per_item_price": "50.00"
                }
            ]
        }
        # In baseline, SaleItem.save() raises ValidationError which causes uncaught exception or 400
        with self.assertRaises(ValidationError):
            self.client.post("/api/sales/create/", payload, format="json")

    def test_get_sales_and_single_sale(self):
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "250.00",
            "payment_mode": "Cash",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "5.00",
                    "per_item_price": "50.00"
                }
            ]
        }
        res_create = self.client.post("/api/sales/create/", payload, format="json")
        sale_id = res_create.data["id"]

        res_list = self.client.get("/api/sales/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res_list.data), 1)

        res_get = self.client.get(f"/api/sales/{sale_id}/")
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data["id"], sale_id)
        self.assertEqual(len(res_get.data["items"]), 1)
