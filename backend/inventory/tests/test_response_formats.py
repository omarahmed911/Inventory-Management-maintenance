from rest_framework import status
from decimal import Decimal
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Sale, SaleItem, Purchase, PurchaseItem


class ResponseFormatsBaselineTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_user_response_format(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_fields = {"id", "username", "first_name", "email", "role", "phone", "profile_image", "is_active", "permissions"}
        self.assertTrue(expected_fields.issubset(set(response.data.keys())))

    def test_category_response_format(self):
        response = self.client.get("/api/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        item = response.data[0]
        expected_fields = {"id", "name", "product_count", "created_at"}
        self.assertTrue(expected_fields.issubset(set(item.keys())))

    def test_unit_response_format(self):
        response = self.client.get("/api/units/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        item = response.data[0]
        expected_fields = {"id", "name", "short_name", "unit_type", "created_at"}
        self.assertTrue(expected_fields.issubset(set(item.keys())))

    def test_party_response_format(self):
        response = self.client.get("/api/parties/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        item = response.data[0]
        expected_fields = {"id", "name", "party_type", "phone", "email", "address", "created_at"}
        self.assertTrue(expected_fields.issubset(set(item.keys())))

    def test_product_response_format(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        item = response.data[0]
        expected_fields = {
            "id", "product_name", "supplier", "supplier_name",
            "category", "category_name", "unit", "unit_name", "unit_short_name", "unit_type",
            "conversion_factor", "cost_price", "selling_price", "minimum_stock", "maximum_stock",
            "stock_quantity", "image", "total_purchased", "total_sold", "created_at", "stock_percent"
        }
        self.assertTrue(expected_fields.issubset(set(item.keys())))

    def test_sale_response_format(self):
        payload = {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "100.00",
            "payment_mode": "Cash",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "2.00",
                    "per_item_price": "50.00"
                }
            ]
        }
        res_create = self.client.post("/api/sales/create/", payload, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        sale_data = res_create.data
        expected_sale_fields = {"id", "invoice_no", "customer", "customer_name", "worker", "worker_name", "total_amount", "payment_mode", "created_at", "items"}
        self.assertTrue(expected_sale_fields.issubset(set(sale_data.keys())))
        self.assertTrue(len(sale_data["items"]) > 0)
        item = sale_data["items"][0]
        expected_item_fields = {"id", "product", "product_name", "quantity", "per_item_price", "total_price", "unit_short_name", "sub_unit_short_name", "conversion_factor"}
        self.assertTrue(expected_item_fields.issubset(set(item.keys())))

    def test_purchase_response_format(self):
        payload = {
            "supplier": self.supplier.id,
            "total_amount": "200.00",
            "paid_amount": "200.00",
            "payment_type": "Cash",
            "items": [
                {
                    "product": self.product.id,
                    "quantity": "5.00",
                    "price": "40.00"
                }
            ]
        }
        res_create = self.client.post("/api/purchases/create/", payload, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        purchase_data = res_create.data
        expected_fields = {"id", "purchase_no", "supplier", "supplier_name", "total_amount", "paid_amount", "due_amount", "payment_type", "created_at", "items"}
        self.assertTrue(expected_fields.issubset(set(purchase_data.keys())))
        item = purchase_data["items"][0]
        expected_item_fields = {"id", "product", "quantity", "price", "product_name", "unit_short_name"}
        self.assertTrue(expected_item_fields.issubset(set(item.keys())))
