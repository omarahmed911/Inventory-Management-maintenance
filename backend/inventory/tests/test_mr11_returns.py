from rest_framework import status
from decimal import Decimal
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Sale, Purchase, Product, Payment, Activity, SaleReturn, PurchaseReturn


class MR11ReturnsTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_sale_return_restores_stock(self):
        # Initial stock: 100. Create sale of 10 -> stock becomes 90.
        sale_res = self.client.post("/api/sales/create/", {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }, format="json")
        self.assertEqual(sale_res.status_code, status.HTTP_201_CREATED)
        sale_id = sale_res.data["id"]
        sale_item_id = sale_res.data["items"][0]["id"]
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))

        # Return 4 units
        return_payload = {
            "sale": sale_id,
            "reason": "Customer changed mind",
            "items": [
                {
                    "sale_item": sale_item_id,
                    "product": self.product.id,
                    "quantity": "4.00",
                    "refund_price": "50.00"
                }
            ]
        }
        res = self.client.post("/api/returns/sales/create/", return_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["total_refund_amount"], "200.00")

        # Verify stock restored to 94.00
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("94.00"))

    def test_sale_return_adjusts_balance_and_creates_payment(self):
        sale_res = self.client.post("/api/sales/create/", {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Credit",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }, format="json")
        sale_id = sale_res.data["id"]
        sale_item_id = sale_res.data["items"][0]["id"]

        # Process return of 2 units (refund 100.00)
        return_res = self.client.post("/api/returns/sales/create/", {
            "sale": sale_id,
            "reason": "Slight defect",
            "items": [{"sale_item": sale_item_id, "product": self.product.id, "quantity": "2.00", "refund_price": "50.00"}]
        }, format="json")
        self.assertEqual(return_res.status_code, status.HTTP_201_CREATED)
        return_no = return_res.data["return_no"]

        # Verify Payment Debit (Credit Note) created for customer
        payment = Payment.objects.filter(reference_no=return_no).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.party, self.customer)
        self.assertEqual(payment.payment_type, "Debit")
        self.assertEqual(payment.payment_mode, "Credit Note")
        self.assertEqual(payment.amount, Decimal("100.00"))

    def test_sale_return_over_return_rejected(self):
        sale_res = self.client.post("/api/sales/create/", {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }, format="json")
        sale_id = sale_res.data["id"]
        sale_item_id = sale_res.data["items"][0]["id"]

        # Attempt to return 11 units when only 10 were sold
        res = self.client.post("/api/returns/sales/create/", {
            "sale": sale_id,
            "items": [{"sale_item": sale_item_id, "product": self.product.id, "quantity": "11.00", "refund_price": "50.00"}]
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("90.00"))

    def test_sale_return_cumulative_validation(self):
        sale_res = self.client.post("/api/sales/create/", {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }, format="json")
        sale_id = sale_res.data["id"]
        sale_item_id = sale_res.data["items"][0]["id"]

        # First return: 6 units (OK)
        res1 = self.client.post("/api/returns/sales/create/", {
            "sale": sale_id,
            "items": [{"sale_item": sale_item_id, "product": self.product.id, "quantity": "6.00", "refund_price": "50.00"}]
        }, format="json")
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Second return: 4 units (OK, total now 10)
        res2 = self.client.post("/api/returns/sales/create/", {
            "sale": sale_id,
            "items": [{"sale_item": sale_item_id, "product": self.product.id, "quantity": "4.00", "refund_price": "50.00"}]
        }, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

        # Third return: 1 unit (fails, only 0 remaining)
        res3 = self.client.post("/api/returns/sales/create/", {
            "sale": sale_id,
            "items": [{"sale_item": sale_item_id, "product": self.product.id, "quantity": "1.00", "refund_price": "50.00"}]
        }, format="json")
        self.assertEqual(res3.status_code, status.HTTP_400_BAD_REQUEST)

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("100.00"))

    def test_purchase_return_reduces_stock(self):
        # Product stock starts at 100.
        # Create purchase of 20 -> stock becomes 120.
        pur_res = self.client.post("/api/purchases/create/", {
            "supplier": self.supplier.id,
            "payment_type": "Cash",
            "paid_amount": "600.00",
            "items": [{"product": self.product.id, "quantity": "20.00", "price": "30.00"}]
        }, format="json")
        self.assertEqual(pur_res.status_code, status.HTTP_201_CREATED)
        purchase_id = pur_res.data["id"]
        purchase_item_id = pur_res.data["items"][0]["id"]
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("120.00"))

        # Return 5 units to supplier
        res = self.client.post("/api/returns/purchases/create/", {
            "purchase": purchase_id,
            "reason": "Overdelivered items",
            "items": [{"purchase_item": purchase_item_id, "product": self.product.id, "quantity": "5.00", "refund_price": "30.00"}]
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["total_refund_amount"], "150.00")

        # Verify stock reduced to 115.00
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, Decimal("115.00"))

    def test_purchase_return_adjusts_balance_and_creates_payment(self):
        pur_res = self.client.post("/api/purchases/create/", {
            "supplier": self.supplier.id,
            "payment_type": "Credit",
            "paid_amount": "0.00",
            "items": [{"product": self.product.id, "quantity": "20.00", "price": "30.00"}]
        }, format="json")
        purchase_id = pur_res.data["id"]
        purchase_item_id = pur_res.data["items"][0]["id"]

        # Return 5 units
        ret_res = self.client.post("/api/returns/purchases/create/", {
            "purchase": purchase_id,
            "reason": "Return damaged goods",
            "items": [{"purchase_item": purchase_item_id, "product": self.product.id, "quantity": "5.00", "refund_price": "30.00"}]
        }, format="json")
        self.assertEqual(ret_res.status_code, status.HTTP_201_CREATED)
        return_no = ret_res.data["return_no"]

        # Verify Payment Credit (Debit Note) created for supplier
        payment = Payment.objects.filter(reference_no=return_no).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.party, self.supplier)
        self.assertEqual(payment.payment_type, "Credit")
        self.assertEqual(payment.payment_mode, "Debit Note")
        self.assertEqual(payment.amount, Decimal("150.00"))

    def test_purchase_return_insufficient_stock_rejected(self):
        pur_res = self.client.post("/api/purchases/create/", {
            "supplier": self.supplier.id,
            "payment_type": "Cash",
            "paid_amount": "600.00",
            "items": [{"product": self.product.id, "quantity": "20.00", "price": "30.00"}]
        }, format="json")
        purchase_id = pur_res.data["id"]
        purchase_item_id = pur_res.data["items"][0]["id"]

        # Artificially set stock to 2 units
        self.product.stock_quantity = Decimal("2.00")
        self.product.save()

        # Attempt to return 5 units -> insufficient stock
        res = self.client.post("/api/returns/purchases/create/", {
            "purchase": purchase_id,
            "items": [{"purchase_item": purchase_item_id, "product": self.product.id, "quantity": "5.00", "refund_price": "30.00"}]
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_activity_logged(self):
        sale_res = self.client.post("/api/sales/create/", {
            "customer": self.customer.id,
            "worker": self.owner_user.id,
            "total_amount": "500.00",
            "payment_mode": "Cash",
            "items": [{"product": self.product.id, "quantity": "10.00", "per_item_price": "50.00"}]
        }, format="json")
        sale_id = sale_res.data["id"]
        sale_item_id = sale_res.data["items"][0]["id"]

        ret_res = self.client.post("/api/returns/sales/create/", {
            "sale": sale_id,
            "items": [{"sale_item": sale_item_id, "product": self.product.id, "quantity": "2.00", "refund_price": "50.00"}]
        }, format="json")
        self.assertEqual(ret_res.status_code, status.HTTP_201_CREATED)
        return_no = ret_res.data["return_no"]

        activity = Activity.objects.filter(action__icontains=return_no).first()
        self.assertIsNotNone(activity)
        self.assertIn("Create Sale Return", activity.action)

    def test_returns_endpoints_unauthenticated_forbidden(self):
        self.client.logout()
        res_sales = self.client.get("/api/returns/sales/")
        self.assertIn(res_sales.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        res_purchases = self.client.get("/api/returns/purchases/")
        self.assertIn(res_purchases.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
