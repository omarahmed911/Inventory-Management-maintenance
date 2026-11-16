from rest_framework import status
from decimal import Decimal
from django.core.exceptions import ValidationError
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Sale, SaleItem, Product, Unit, Category
from unittest.mock import patch


class MR03SaleEditDeleteTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_sale_edit_increase_quantity(self):
        # Product stock starts at 100
        # Create sale of 10 -> stock becomes 90
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }
        res = self.client.post("/api/sales/create/", payload, format="json")
        sale_id = res.data["id"]
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))

        # Update sale to 15 -> stock should restore 10 and deduct 15 -> final stock 85
        update_payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "750.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "15.00", "per_item_price": "50.00"}]
        }
        res_update = self.client.put(f"/api/sales/update/{sale_id}/", update_payload, format="json")
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("85.00"))

    def test_sale_edit_decrease_quantity(self):
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }
        res = self.client.post("/api/sales/create/", payload, format="json")
        sale_id = res.data["id"]
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))

        # Update sale to 4 -> stock should restore 10 and deduct 4 -> final stock 96
        update_payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "200.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "4.00", "per_item_price": "50.00"}]
        }
        res_update = self.client.put(f"/api/sales/update/{sale_id}/", update_payload, format="json")
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("96.00"))

    def test_delete_sale_restores_stock(self):
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }
        res = self.client.post("/api/sales/create/", payload, format="json")
        sale_id = res.data["id"]
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))

        # Delete sale -> stock should restore to 100
        res_del = self.client.delete(f"/api/sales/delete/{sale_id}/")
        self.assertEqual(res_del.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("100.00"))

    def test_delete_single_item_restores_stock(self):
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }
        res = self.client.post("/api/sales/create/", payload, format="json")
        sale = Sale.objects.get(id=res.data["id"])
        item = sale.items.first()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))

        # Delete single item
        item.delete()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("100.00"))

    def test_insufficient_stock_on_update_rolls_back(self):
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }
        res = self.client.post("/api/sales/create/", payload, format="json")
        sale_id = res.data["id"]
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))

        # Try updating to 200 (stock is only 100 total)
        update_payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "10000.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "200.00", "per_item_price": "50.00"}]
        }
        res_update = self.client.put(f"/api/sales/update/{sale_id}/", update_payload, format="json")
        self.assertEqual(res_update.status_code, status.HTTP_400_BAD_REQUEST)

        # After rollback: stock must remain 90, item must remain 10
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))
        sale = Sale.objects.get(id=sale_id)
        self.assertEqual(sale.items.count(), 1)
        self.assertEqual(sale.items.first().quantity, Decimal("10.00"))

    def test_missing_product_fails_cleanly(self):
        sale = Sale.objects.create(customer=self.customer, worker=self.owner_user, total_amount=0)
        item = SaleItem(sale=sale, product=None, quantity=Decimal("5.00"), per_item_price=Decimal("10.00"))
        with self.assertRaises(ValidationError):
            item.save()

    def test_rollback_on_simulated_failure(self):
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }
        res = self.client.post("/api/sales/create/", payload, format="json")
        sale_id = res.data["id"]
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))

        update_payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "600.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "12.00", "per_item_price": "50.00"}]
        }

        # Simulate exception during item creation inside update
        with patch.object(SaleItem.objects, "create", side_effect=RuntimeError("Simulated crash")):
            with self.assertRaises(RuntimeError):
                self.client.put(f"/api/sales/update/{sale_id}/", update_payload, format="json")

        # Verify stock and items rolled back
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))
        sale = Sale.objects.get(id=sale_id)
        self.assertEqual(sale.items.count(), 1)
        self.assertEqual(sale.items.first().quantity, Decimal("10.00"))
