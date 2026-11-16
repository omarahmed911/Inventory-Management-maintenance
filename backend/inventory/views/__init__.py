# Re-export all views to preserve backward compatibility for urls.py and tests

from .pagination import OptionalPagination, paginate_if_requested
from .auth import (
    login_view, logout_view, csrf_cookie, get_current_user
)
from .users import (
    create_user, get_users, get_single_user, update_user,
    verify_old_password, toggle_user_status, delete_user,
    request_password_change, get_password_requests,
    approve_password_request, decline_password_request,
    check_password_request_status, request_account_resume, resume_account
)
from .roles import (
    get_roles, create_role, update_role_permissions,
    delete_role, apply_role_defaults_to_user, user_permissions
)
from .catalog import (
    get_categories, get_category, create_category, update_category, delete_category,
    get_units, get_unit, create_unit, update_unit, delete_unit,
    get_parties, get_party, create_party, update_party, delete_party,
    get_products, get_product, create_product, update_product, delete_product
)
from .sales import (
    get_sales, get_sale, create_sale, update_sale, delete_sale
)
from .purchases import (
    get_purchases, get_purchase, create_purchase
)
from .stock import (
    add_damaged_stock, adjust_stock, get_activities
)
from .returns import (
    get_sale_returns, create_sale_return, get_purchase_returns, create_purchase_return
)
from .dashboard import (
    get_dashboard_data, get_all_transactions, get_payments
)

__all__ = [
    'OptionalPagination', 'paginate_if_requested',
    'login_view', 'logout_view', 'csrf_cookie', 'get_current_user',
    'create_user', 'get_users', 'get_single_user', 'update_user',
    'verify_old_password', 'toggle_user_status', 'delete_user',
    'request_password_change', 'get_password_requests',
    'approve_password_request', 'decline_password_request',
    'check_password_request_status', 'request_account_resume', 'resume_account',
    'get_roles', 'create_role', 'update_role_permissions',
    'delete_role', 'apply_role_defaults_to_user', 'user_permissions',
    'get_categories', 'get_category', 'create_category', 'update_category', 'delete_category',
    'get_units', 'get_unit', 'create_unit', 'update_unit', 'delete_unit',
    'get_parties', 'get_party', 'create_party', 'update_party', 'delete_party',
    'get_products', 'get_product', 'create_product', 'update_product', 'delete_product',
    'get_sales', 'get_sale', 'create_sale', 'update_sale', 'delete_sale',
    'get_purchases', 'get_purchase', 'create_purchase',
    'get_sale_returns', 'create_sale_return', 'get_purchase_returns', 'create_purchase_return',
    'add_damaged_stock', 'adjust_stock', 'get_activities',
    'get_dashboard_data', 'get_all_transactions', 'get_payments'
]
