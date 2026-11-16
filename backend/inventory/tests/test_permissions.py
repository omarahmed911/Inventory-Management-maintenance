from rest_framework import status
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Permission


class PermissionsBaselineTests(BaseInventoryTestCase):
    def test_owner_bypasses_all_permission_checks(self):
        self.client.force_login(self.owner_user)
        # Owner can view products, sales, purchases, categories
        res_prod = self.client.get("/api/products/")
        self.assertEqual(res_prod.status_code, status.HTTP_200_OK)

        res_sales = self.client.get("/api/sales/")
        self.assertEqual(res_sales.status_code, status.HTTP_200_OK)

        res_purchases = self.client.get("/api/purchases/")
        self.assertEqual(res_purchases.status_code, status.HTTP_200_OK)

        res_categories = self.client.get("/api/categories/")
        self.assertEqual(res_categories.status_code, status.HTTP_200_OK)

    def test_employee_allowed_modules(self):
        self.client.force_login(self.employee_user)
        # Employee has permission for sales view
        res = self.client.get("/api/sales/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_employee_denied_modules(self):
        self.client.force_login(self.employee_user)
        # Employee does NOT have permission for purchases
        res_purchases = self.client.get("/api/purchases/")
        self.assertEqual(res_purchases.status_code, status.HTTP_403_FORBIDDEN)

        # Employee does NOT have permission for categories
        res_categories = self.client.get("/api/categories/")
        self.assertEqual(res_categories.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access_denied(self):
        res = self.client.get("/api/products/")
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_apply_role_defaults_by_owner(self):
        self.client.force_login(self.owner_user)
        # Delete employee's permissions
        Permission.objects.filter(user=self.employee_user).delete()
        self.assertEqual(Permission.objects.filter(user=self.employee_user).count(), 0)

        res = self.client.post(f"/api/permissions/apply-defaults/{self.employee_user.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertGreater(Permission.objects.filter(user=self.employee_user).count(), 0)

    def test_apply_role_defaults_by_non_owner_forbidden(self):
        self.client.force_login(self.manager_user)
        res = self.client.post(f"/api/permissions/apply-defaults/{self.employee_user.id}/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_user_permissions(self):
        self.client.force_login(self.owner_user)
        res = self.client.get(f"/api/permissions/{self.employee_user.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
