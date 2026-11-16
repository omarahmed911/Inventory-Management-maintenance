from rest_framework import status
from decimal import Decimal
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Product, Category, Unit, Party


class ProductsBaselineTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_get_products(self):
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product_name"], "Rice")

    def test_get_single_product(self):
        response = self.client.get(f"/api/products/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["product_name"], "Rice")
        self.assertEqual(Decimal(str(response.data["stock_quantity"])), Decimal("100.00"))

    def test_create_product(self):
        payload = {
            "product_name": "Wheat",
            "supplier": self.supplier.id,
            "category": self.category_food.id,
            "unit": self.unit_kg.id,
            "cost_price": "30.00",
            "selling_price": "45.00",
            "minimum_stock": 5,
            "maximum_stock": 200,
            "stock_quantity": "50.00"
        }
        response = self.client.post("/api/products/create/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["product_name"], "Wheat")
        self.assertTrue(Product.objects.filter(product_name="Wheat").exists())

    def test_update_product(self):
        payload = {
            "product_name": "Basmati Rice",
            "supplier": self.supplier.id,
            "category": self.category_food.id,
            "unit": self.unit_kg.id,
            "cost_price": "50.00",
            "selling_price": "70.00",
            "minimum_stock": 15,
            "maximum_stock": 600,
            "stock_quantity": "100.00"
        }
        response = self.client.put(f"/api/products/update/{self.product.id}/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.product_name, "Basmati Rice")
        self.assertEqual(self.product.selling_price, Decimal("70.00"))

    def test_delete_product(self):
        response = self.client.delete(f"/api/products/delete/{self.product.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_product_stock_percent(self):
        self.assertEqual(self.product.stock_percent, 20)  # 100 / 500 * 100 = 20%

    def test_categories_crud(self):
        res_list = self.client.get("/api/categories/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        res_create = self.client.post("/api/categories/create/", {"name": "Electronics"}, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)

        cat_id = res_create.data["id"]
        res_update = self.client.put(f"/api/categories/update/{cat_id}/", {"name": "Consumer Electronics"}, format="json")
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)

        res_delete = self.client.delete(f"/api/categories/delete/{cat_id}/")
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_units_crud(self):
        res_list = self.client.get("/api/units/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        res_create = self.client.post("/api/units/create/", {"name": "Liter", "short_name": "L", "unit_type": "Decimal"}, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)

        unit_id = res_create.data["id"]
        res_update = self.client.put(f"/api/units/update/{unit_id}/", {"name": "Litres", "short_name": "l", "unit_type": "Decimal"}, format="json")
        self.assertEqual(res_update.status_code, status.HTTP_200_OK)

        res_delete = self.client.delete(f"/api/units/delete/{unit_id}/")
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)

    def test_parties_crud(self):
        res_list = self.client.get("/api/parties/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        res_create = self.client.post("/api/parties/create/", {
            "name": "New Client",
            "party_type": "Customer",
            "phone": "5551234",
            "email": "client@test.com",
            "address": "123 Main St"
        }, format="json")
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)

        party_id = res_create.data["id"]
        res_get = self.client.get(f"/api/parties/{party_id}/")
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)

        res_delete = self.client.delete(f"/api/parties/delete/{party_id}/")
        self.assertEqual(res_delete.status_code, status.HTTP_204_NO_CONTENT)
