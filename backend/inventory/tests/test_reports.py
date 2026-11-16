from rest_framework import status
from decimal import Decimal
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Sale, SaleItem, Purchase, PurchaseItem, Payment


class ReportsBaselineTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_current_stock_report(self):
        response = self.client.get("/api/reports/current-stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_low_stock_report(self):
        response = self.client.get("/api/reports/low-stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_out_of_stock_report(self):
        response = self.client.get("/api/reports/out-of-stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_sales_summary_report(self):
        response = self.client.get("/api/reports/sales-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("invoices", response.data)
        self.assertIn("products", response.data)

    def test_product_wise_sales_report(self):
        response = self.client.get("/api/reports/product-sales/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_sales_report(self):
        response = self.client.get("/api/reports/customer-sales/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_purchase_summary_report(self):
        response = self.client.get("/api/reports/purchase-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_supplier_purchase_report(self):
        response = self.client.get("/api/reports/supplier-purchase/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_profit_loss_report(self):
        response = self.client.get("/api/reports/profit-loss/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_sales", response.data)
        self.assertIn("total_purchase", response.data)
        self.assertIn("profit", response.data)

    def test_payment_report(self):
        response = self.client.get("/api/reports/payment/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_outstanding_report(self):
        response = self.client.get("/api/reports/customer-outstanding/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_stock_movement_report(self):
        response = self.client.get("/api/reports/stock-movement/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
