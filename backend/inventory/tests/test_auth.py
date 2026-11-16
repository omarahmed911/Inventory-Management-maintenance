from rest_framework import status
from django.contrib.auth.models import User
from inventory.tests.test_base import BaseInventoryTestCase


class AuthBaselineTests(BaseInventoryTestCase):
    def test_csrf_cookie(self):
        response = self.client.get("/api/auth/csrf-cookie/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("csrfToken", response.data)

    def test_login_success(self):
        response = self.client.post("/api/auth/login/", {
            "username": "owner",
            "password": "ownerpass"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "owner")
        self.assertEqual(response.data["role"], "Owner")

    def test_login_invalid_credentials(self):
        response = self.client.post("/api/auth/login/", {
            "username": "owner",
            "password": "wrongpassword"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_login_account_on_hold(self):
        user = self.create_user("holduser", "holdpass", "Employee")
        user.is_active = False
        user.save()

        response = self.client.post("/api/auth/login/", {
            "username": "holduser",
            "password": "holdpass"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data.get("error"), "account_hold")

    def test_logout_authenticated(self):
        self.client.force_login(self.owner_user)
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Logged out successfully")

    def test_logout_unauthenticated(self):
        response = self.client.post("/api/auth/logout/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_get_current_user_authenticated(self):
        self.client.force_login(self.manager_user)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "manager")
        self.assertEqual(response.data["role"], "Manager")
        self.assertIn("permissions", response.data)

    def test_get_current_user_unauthenticated(self):
        response = self.client.get("/api/auth/me/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
