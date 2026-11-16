from rest_framework import status
from decimal import Decimal
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Sale, SaleItem, Purchase, PurchaseItem


class DashboardBaselineTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_dashboard_data_structure(self):
        # Create a sale and purchase to populate data
        Sale.objects.create(
            customer=self.customer,
            worker=self.owner_user,
            total_amount=Decimal("150.00"),
            payment_mode="Cash"
        )
        Purchase.objects.create(
            supplier=self.supplier,
            total_amount=Decimal("100.00"),
            paid_amount=Decimal("100.00"),
            payment_type="Cash"
        )

        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn("total_products", data)
        self.assertIn("products", data)
        self.assertIn("low_stock_count", data)
        self.assertIn("category_count", data)
        self.assertIn("sales", data)
        self.assertIn("purchases", data)
        self.assertIn("profit_loss", data)
        self.assertIn("customer_outstanding", data)
        self.assertIn("current_stock", data)
        self.assertIn("parties", data)

        self.assertEqual(data["profit_loss"]["total_sales"], Decimal("150.00"))
        self.assertEqual(data["profit_loss"]["total_purchase"], Decimal("100.00"))
        self.assertEqual(data["profit_loss"]["profit"], Decimal("50.00"))

    def test_dashboard_permission_denied_for_unauthorized_user(self):
        self.client.force_login(self.employee_user)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
