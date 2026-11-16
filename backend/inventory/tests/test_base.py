from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from decimal import Decimal
from inventory.models import (
    UserProfile, Role, RolePermission, Permission,
    Category, Unit, Party, Product, Sale, SaleItem,
    Purchase, PurchaseItem, Payment, DamagedStock, StockAdjustment, Activity
)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class BaseInventoryTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create system roles if not present
        self.owner_role, _ = Role.objects.get_or_create(name="Owner", defaults={"is_system": True})
        self.manager_role, _ = Role.objects.get_or_create(name="Manager", defaults={"is_system": True})
        self.supervisor_role, _ = Role.objects.get_or_create(name="Supervisor", defaults={"is_system": True})
        self.employee_role, _ = Role.objects.get_or_create(name="Employee", defaults={"is_system": True})

        # Create users
        self.owner_user = self.create_user("owner", "ownerpass", "Owner")
        self.manager_user = self.create_user("manager", "managerpass", "Manager")
        self.supervisor_user = self.create_user("supervisor", "superpass", "Supervisor")
        self.employee_user = self.create_user("employee", "employeepass", "Employee")

        # Create master data
        self.unit_kg = Unit.objects.create(name="Kilogram", short_name="kg", unit_type="Decimal")
        self.unit_pcs = Unit.objects.create(name="Pieces", short_name="pcs", unit_type="Integer")
        self.category_food = Category.objects.create(name="Food")
        self.supplier = Party.objects.create(name="Test Supplier", party_type="Supplier", phone="1234567890", email="sup@test.com")
        self.customer = Party.objects.create(name="Test Customer", party_type="Customer", phone="0987654321", email="cust@test.com")

        self.product = Product.objects.create(
            product_name="Rice",
            supplier=self.supplier,
            category=self.category_food,
            unit=self.unit_kg,
            cost_price=Decimal("40.00"),
            selling_price=Decimal("50.00"),
            minimum_stock=10,
            maximum_stock=500,
            stock_quantity=Decimal("100.00")
        )

    def create_user(self, username, password, role_name):
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=username.capitalize(),
            email=f"{username}@example.com"
        )
        UserProfile.objects.create(user=user, role=role_name)
        role = Role.objects.filter(name=role_name).first()
        if role:
            for rp in role.default_permissions.all():
                perm = Permission.objects.create(
                    user=user,
                    module=rp.module,
                    can_view=rp.can_view,
                    can_create=rp.can_create,
                    can_update=rp.can_update,
                    can_delete=rp.can_delete,
                )
                if rp.module == "dashboard":
                    perm.set_dashboard_fields_list(rp.get_dashboard_fields_list())
                    perm.save()
        return user
