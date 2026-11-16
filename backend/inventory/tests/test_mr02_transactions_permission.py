from rest_framework import status
from inventory.tests.test_base import BaseInventoryTestCase


class MR02TransactionsPermissionTests(BaseInventoryTestCase):
    def test_anonymous_access_transactions_denied(self):
        response = self.client.get("/api/transactions/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_unauthorized_user_transactions_denied(self):
        # Employee does not have 'payments' permission
        self.client.force_login(self.employee_user)
        response = self.client.get("/api/transactions/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authorized_user_transactions_allowed(self):
        # Owner has full access
        self.client.force_login(self.owner_user)
        response = self.client.get("/api/transactions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Manager has payments view permission
        self.client.force_login(self.manager_user)
        response_mgr = self.client.get("/api/transactions/")
        self.assertEqual(response_mgr.status_code, status.HTTP_200_OK)

    def test_public_endpoints_still_accessible(self):
        res_csrf = self.client.get("/api/auth/csrf-cookie/")
        self.assertEqual(res_csrf.status_code, status.HTTP_200_OK)

        res_login = self.client.post("/api/auth/login/", {
            "username": "owner",
            "password": "wrongpassword"
        }, format="json")
        self.assertEqual(res_login.status_code, status.HTTP_400_BAD_REQUEST)
