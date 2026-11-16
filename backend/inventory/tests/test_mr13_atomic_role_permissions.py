from rest_framework import status
from unittest.mock import patch
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import Role, RolePermission, Permission


class MR13AtomicRolePermissionsTests(BaseInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner_user)

    def test_update_role_permissions_success(self):
        payload = {
            "permissions": {
                "products": {"view": True, "create": True, "update": False, "delete": False},
                "sales": {"view": True, "create": False, "update": False, "delete": False}
            }
        }
        res = self.client.put(f"/api/roles/update/{self.manager_role.id}/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["updated_users"], 1)

        # Verify RolePermission
        self.assertEqual(self.manager_role.default_permissions.count(), 2)
        # Verify Manager user has the permissions
        self.assertEqual(Permission.objects.filter(user=self.manager_user).count(), 2)

    def test_update_role_permissions_empty(self):
        payload = {"permissions": {}}
        res = self.client.put(f"/api/roles/update/{self.manager_role.id}/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(self.manager_role.default_permissions.count(), 0)
        self.assertEqual(Permission.objects.filter(user=self.manager_user).count(), 0)

    def test_update_role_permissions_invalid_input(self):
        initial_role_perms = self.manager_role.default_permissions.count()
        initial_user_perms = Permission.objects.filter(user=self.manager_user).count()

        payload = {"permissions": "invalid_string_not_dict"}
        res = self.client.put(f"/api/roles/update/{self.manager_role.id}/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Existing permissions must not be wiped out!
        self.manager_role.refresh_from_db()
        self.assertEqual(self.manager_role.default_permissions.count(), initial_role_perms)
        self.assertEqual(Permission.objects.filter(user=self.manager_user).count(), initial_user_perms)

    def test_simulated_mid_operation_failure_rolls_back(self):
        initial_role_perms = self.manager_role.default_permissions.count()
        initial_user_perms = Permission.objects.filter(user=self.manager_user).count()

        payload = {
            "permissions": {
                "products": {"view": True, "create": True, "update": True, "delete": True}
            }
        }

        # Mock Permission.objects.create to raise an exception mid-operation
        with patch.object(Permission.objects, "create", side_effect=RuntimeError("DB error while updating user")):
            with self.assertRaises(RuntimeError):
                self.client.put(f"/api/roles/update/{self.manager_role.id}/", payload, format="json")

        # After rollback, initial role permissions and user permissions must be restored!
        self.manager_role.refresh_from_db()
        self.assertEqual(self.manager_role.default_permissions.count(), initial_role_perms)
        self.assertEqual(Permission.objects.filter(user=self.manager_user).count(), initial_user_perms)
