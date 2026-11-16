from django.test import TransactionTestCase, override_settings
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from rest_framework.test import APIClient
import threading
from inventory.models import (
    Product, Unit, Category, Party, Sale, SaleItem,
    DamagedStock, StockAdjustment, UserProfile
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class MR05StockRaceConditionTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="owner5", password="pwd")
        UserProfile.objects.create(user=self.user, role="Owner")
        self.unit = Unit.objects.create(name="Kg", short_name="kg", unit_type="Decimal")
        self.category = Category.objects.create(name="Food5")
        self.supplier = Party.objects.create(name="Sup5", party_type="Supplier")
        self.customer = Party.objects.create(name="Cust5", party_type="Customer")
        self.product = Product.objects.create(
            product_name="Sugar",
            supplier=self.supplier,
            category=self.category,
            unit=self.unit,
            stock_quantity=Decimal("10.00"),
            cost_price=Decimal("20.00"),
            selling_price=Decimal("30.00"),
            minimum_stock=2,
            maximum_stock=100
        )

    def test_damaged_stock_cannot_exceed_available(self):
        damaged = DamagedStock(product=self.product, quantity=Decimal("15.00"), reason="Water damage")
        with self.assertRaises(ValidationError):
            damaged.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("10.00"))

    def test_stock_adjustment_cannot_drive_negative(self):
        adj = StockAdjustment(
            product=self.product,
            old_quantity=Decimal("10.00"),
            new_quantity=Decimal("-5.00"),
            reason="Invalid count"
        )
        with self.assertRaises(ValidationError):
            adj.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("10.00"))

    def test_sale_cannot_drive_negative(self):
        sale = Sale.objects.create(customer=self.customer, worker=self.user, total_amount=Decimal("300.00"))
        item = SaleItem(sale=sale, product=self.product, quantity=Decimal("15.00"), per_item_price=Decimal("20.00"))
        with self.assertRaises(ValidationError):
            item.save()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("10.00"))

    def test_concurrent_sales_cannot_oversell(self):
        # Product has 10 units in stock.
        # Two threads simultaneously try to sell 10 units each.
        results = []
        errors = []

        def make_sale(thread_id):
            client = APIClient()
            client.force_authenticate(user=self.user)
            payload = {
                "customer": self.customer.id,
                "worker": self.user.id,
                "total_amount": "300.00",
                "payment_mode": "Cash",
                "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "30.00"}]
            }
            try:
                res = client.post("/api/sales/create/", payload, format="json")
                results.append((thread_id, res.status_code))
            except Exception as e:
                errors.append((thread_id, type(e).__name__))

        t1 = threading.Thread(target=make_sale, args=(1,))
        t2 = threading.Thread(target=make_sale, args=(2,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.product.refresh_from_db()
        # Stock must never be negative!
        self.assertGreaterEqual(self.product.stock_quantity, Decimal("0.00"))
        # At most 1 sale could have succeeded for 10 units from 10 initial stock
        success_count = sum(1 for _, code in results if code == 201)
        self.assertLessEqual(success_count, 1)
