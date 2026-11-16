from rest_framework import status
from inventory.tests.test_base import BaseInventoryTestCase
from inventory.models import UserProfile, Permission


class MR01UserAuthorizationTests(BaseInventoryTestCase):
    def test_cross_account_update_rejected(self):
        # Employee attempts to update supervisor
        self.client.force_login(self.employee_user)
        response = self.client.put(f"/api/users/update/{self.supervisor_user.id}/", {
            "first_name": "HackedName"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.supervisor_user.refresh_from_db()
        self.assertNotEqual(self.supervisor_user.first_name, "HackedName")

    def test_role_change_by_non_admin_rejected(self):
        # Employee attempts to escalate own role to Owner
        self.client.force_login(self.employee_user)
        response = self.client.put(f"/api/users/update/{self.employee_user.id}/", {
            "first_name": "Employee",
            "role": "Owner"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.employee_user.userprofile.refresh_from_db()
        self.assertEqual(self.employee_user.userprofile.role, "Employee")

    def test_own_profile_update_allowed(self):
        self.client.force_login(self.employee_user)
        response = self.client.put(f"/api/users/update/{self.employee_user.id}/", {
            "first_name": "UpdatedEmployee",
            "email": "updated@example.com",
            "phone": "9999999999"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_user.refresh_from_db()
        self.assertEqual(self.employee_user.first_name, "UpdatedEmployee")
        self.assertEqual(self.employee_user.email, "updated@example.com")

    def test_admin_update_other_user_and_role_allowed(self):
        # Owner updates employee's role to Supervisor
        self.client.force_login(self.owner_user)
        response = self.client.put(f"/api/users/update/{self.employee_user.id}/", {
            "first_name": "PromotedEmployee",
            "role": "Supervisor"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.employee_user.refresh_from_db()
        self.employee_user.userprofile.refresh_from_db()
        self.assertEqual(self.employee_user.first_name, "PromotedEmployee")
        self.assertEqual(self.employee_user.userprofile.role, "Supervisor")

    def test_verify_password_own_account_success(self):
        self.client.force_login(self.employee_user)
        response = self.client.post(f"/api/users/verify-password/{self.employee_user.id}/", {
            "old_password": "employeepass"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password verified")

    def test_verify_password_own_account_incorrect(self):
        self.client.force_login(self.employee_user)
        response = self.client.post(f"/api/users/verify-password/{self.employee_user.id}/", {
            "old_password": "wrongpass"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_password_other_account_forbidden(self):
        # Employee attempts to guess supervisor's password
        self.client.force_login(self.employee_user)
        response = self.client.post(f"/api/users/verify-password/{self.supervisor_user.id}/", {
            "old_password": "superpass"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
