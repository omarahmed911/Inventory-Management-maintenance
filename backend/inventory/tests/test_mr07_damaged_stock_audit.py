from rest_framework import status
from decimal import Decimal
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Activity, DamagedStock


class MR07DamagedStockAuditTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_damaged_stock_creation_creates_activity_log(self):
        initial_activity_count = Activity.objects.count()

        payload = {
            "product": self.product.id,
            "quantity": "5.00",
            "reason": "Expired"
        }
        response = self.client.post("/api/damaged-stocks/", payload, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

        # Verify Activity log created
        self.assertEqual(Activity.objects.count(), initial_activity_count + 1)
        activity = Activity.objects.latest("created_at")
        self.assertEqual(activity.user, self.owner_user)
        self.assertIn("Damaged Stock", activity.action)
        self.assertIn(self.product.product_name, activity.action)
