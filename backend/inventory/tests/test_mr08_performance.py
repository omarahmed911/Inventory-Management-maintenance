from rest_framework import status
from decimal import Decimal
from django.test.utils import CaptureQueriesContext
from django.db import connection
import time
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Party, Product, Sale, Purchase, Payment, Category, Unit


class MR08PerformanceTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

        # Create 10 customers
        self.customers = []
        for i in range(10):
            c = Party.objects.create(name=f"Customer {i}", party_type="Customer")
            self.customers.append(c)
            # Create a sale and payment for each
            Sale.objects.create(
                customer=c,
                worker=self.owner_user,
                total_amount=Decimal("100.00"),
                payment_mode="Cash"
            )

    def test_dashboard_query_count_and_results(self):
        # Measure dashboard query count and time
        start_time = time.perf_counter()
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/dashboard/")
        duration = time.perf_counter() - start_time

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Outstanding balances should correctly have 10 customer entries
        self.assertEqual(len(response.data["customer_outstanding"]), 11)  # 10 + self.customer
        # With optimized grouped queries, total queries for dashboard should be <= 15 (was 25-30+)
        self.assertLessEqual(len(ctx.captured_queries), 15)

    def test_empty_dataset_dashboard(self):
        # Empty all sales, purchases, payments, products
        Sale.objects.all().delete()
        Purchase.objects.all().delete()
        Payment.objects.all().delete()
        Product.objects.all().delete()
        Party.objects.all().delete()

        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_products"], 0)
        self.assertEqual(response.data["customer_outstanding"], [])
        self.assertEqual(response.data["profit_loss"]["profit"], 0)

    def test_products_list_query_count_select_related(self):
        # Create 10 products
        for i in range(10):
            Product.objects.create(
                product_name=f"Product {i}",
                supplier=self.supplier,
                category=self.category_food,
                unit=self.unit_kg,
                cost_price=Decimal("10.00"),
                selling_price=Decimal("15.00"),
                stock_quantity=Decimal("50.00")
            )

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get("/api/products/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 11)
        # Without select_related, 11 products would trigger 11 * 4 + 1 = 45+ queries.
        # With select_related and subquery annotations, product loading is 1 query (<= 5 total including auth/permission checks)!
        self.assertLessEqual(len(ctx.captured_queries), 5)

    def test_optional_pagination(self):
        # Without ?page param -> returns plain list
        res_unpaginated = self.client.get("/api/products/")
        self.assertEqual(res_unpaginated.status_code, status.HTTP_200_OK)
        self.assertIsInstance(res_unpaginated.data, list)

        # With ?page=1 -> returns paginated object with count and results
        res_paginated = self.client.get("/api/products/?page=1&page_size=5")
        self.assertEqual(res_paginated.status_code, status.HTTP_200_OK)
        self.assertIn("count", res_paginated.data)
        self.assertIn("results", res_paginated.data)
        self.assertEqual(len(res_paginated.data["results"]), 1)  # only self.product initially
