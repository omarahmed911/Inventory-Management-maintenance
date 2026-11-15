# Inventory Management System — Maintenance Reference

> Single source of truth for the maintenance agent. Merged from "Milestone 1 – Analysis & Maintenance Plan" and "Maintenance Plan & Change Record".
> Goal: resolve **all 13 maintenance requests (MR-01 … MR-13)** safely, with tests, and document every change.
> Repository: `Gangatharan2108/Inventory-Management`

---

## 1. System Overview

Inventory Management System for a trading business: products, categories, units, parties (customers/suppliers), purchases, sales, payments, damaged stock, stock adjustments, users, roles and permissions, dashboard, and reports (stock, sales, purchase, payment, profit/loss, outstanding balances).

**Roles:** Owner (full access), Manager, Supervisor, Employee. Access is controlled per module with permissions: view / create / update / delete (assigned through roles).

### 1.1 Tech stack

| Layer | Technology |
|---|---|
| Frontend | React SPA, React Router, shared Axios client (`frontend/src/api/axios.js`) |
| Backend | Django + Django REST Framework, **session authentication + CSRF** (not JWT) |
| Database | SQLite (`backend/db.sqlite3`) via Django ORM |
| Files | `media/`, served by Django in DEBUG |
| Backend libs | Django, DRF, django-cors-headers, python-decouple, widget_tweaks |
| Frontend libs | react, react-dom, react-router-dom, axios, bootstrap, bootstrap-icons, react-bootstrap, react-icons, recharts, exceljs, file-saver, xlsx, tailwindcss |

### 1.2 Architecture (layered, client–server)

- **Presentation:** React pages → service layer `frontend/src/api/*.js` → Axios (cookie + CSRF).
- **API:** DRF views (`views.py`, `views_reports.py`) under `/api/`, protected by custom permission decorators (`permissions.py`).
- **Business/validation:** serializers (`serializers.py`) + model `save()` methods (which apply stock and payment side effects).
- **Data:** Django ORM models on SQLite.

Request flow: React page → API service → Axios → Django URL → permission check → view → serializer/model → SQLite → JSON.

### 1.3 Key files

| File | Responsibility |
|---|---|
| `backend/inventory_system/settings.py` | Django config, CORS/CSRF, DRF auth, SQLite, media/static |
| `backend/inventory_system/urls.py` | Mounts `/api/` to inventory app, serves media in debug |
| `backend/inventory/models.py` | All business tables + stock/payment side effects |
| `backend/inventory/permissions.py` | Custom module/action authorization decorators |
| `backend/inventory/serializers.py` | Validation, nested create/update (users, products, sales, purchases) |
| `backend/inventory/views.py` | Auth, users, permissions, master data, sales, purchases, stock, dashboard (~1,000 lines) |
| `backend/inventory/views_reports.py` | Stock, sales, purchase, payment, profit/loss, outstanding reports |
| `backend/inventory/tests.py` | Currently **empty** |
| `frontend/src/api/axios.js` | Shared client, CSRF, credentials |
| `frontend/src/routes/AppRoutes.jsx`, `ProtectedRoute.jsx` | Routing + client-side permission guard |
| `frontend/src/context/AuthContext.jsx` | Current user + permissions (localStorage) |
| `frontend/src/pages/**` | UI screens |

### 1.4 Database models

| Model | Main columns | Keys / relations |
|---|---|---|
| UserProfile | user, role, phone, address, profile_image | OneToOne → auth.User |
| Permission | user, module, can_view/create/update/delete, dashboard_fields | FK → auth.User |
| Category | name, created_at | name unique |
| Unit | name, short_name, unit_type, created_at | no unique constraint |
| Party | name, party_type, phone, email, address, created_at | Customer or Supplier |
| Product | product_name, supplier, category, unit, sub_unit, conversion_factor, cost_price, selling_price, minimum_stock, maximum_stock, stock_quantity, image, created_at | FK → Party (supplier), Category, Unit |
| Sale | invoice_no, customer, worker, total_amount, payment_mode, created_at | invoice_no unique; FK → Party, User |
| SaleItem | sale, product, quantity, per_item_price | FK → Sale, Product |
| Purchase | purchase_no, supplier, total_amount, paid_amount, due_amount, payment_type, created_at | purchase_no unique; FK → Party |
| PurchaseItem | purchase, product, quantity, price | FK → Purchase, Product |
| Payment | party, payment_type, amount, payment_mode, reference_no, created_at | FK → Party |
| DamagedStock | product, quantity, reason, created_at | FK → Product |
| StockAdjustment | product, old_quantity, new_quantity, reason, adjusted_at, created_at | FK → Product |
| Activity | action, user, created_at | FK → User (nullable) |
| Role | name, is_system, created_at | name unique |
| RolePermission | role, module, can_view/create/update/delete, dashboard_fields | FK → Role; unique (role, module) |
| PasswordChangeRequest | user, status, request_type, message, created_at | FK → User |

### 1.5 Frontend ↔ backend endpoints

- Auth: `/api/auth/csrf-cookie/`, `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/me/`
- Users: `/auth/create/`, `/users/`, `/users/<id>/`, `/users/update/<id>/`, `/users/toggle/<id>/`, `/users/verify-password/<id>/`, `/users/delete/<id>/`
- Roles/permissions: `/roles/*`, `/permissions/*`
- Master data: categories, units, parties, products (CRUD)
- Transactions: `/sales/*`, `/purchases/*`
- Reports/dashboard: `/dashboard/`, `/activities/`, `/payments/`, `/reports/*`

---

## 2. Maintenance Requests (all must be resolved)

Priority legend: Critical > High > Medium > Low.
> Note: findings come from static code review. **Validate each with a test before changing code** (write a failing test first where possible). Do not claim a runtime failure was reproduced unless a test shows it.

### Summary table

| ID | Issue | Type | Priority |
|---|---|---|---|
| MR-01 | `update_user()` only requires login → any user can edit others / change roles; `verify_old_password()` has no ownership check | Corrective | Critical |
| MR-02 | `get_all_transactions` has no permission check; DRF default is `AllowAny` | Corrective | Critical |
| MR-03 | Sale edit/delete doesn't restore stock; update not atomic | Corrective | Critical |
| MR-04 | Insecure production settings | Adaptive | High |
| MR-05 | Stock race condition (oversell) | Corrective | High |
| MR-06 | No automated tests | Preventive | High |
| MR-07 | Damaged stock creation not audit-logged | Corrective | Medium |
| MR-08 | No pagination, N+1 queries, Python-side merge/sort, per-customer dashboard queries | Perfective | Medium |
| MR-09 | README/setup files outdated, no requirements.txt/.env.example, screenshots placeholder | Preventive | Medium |
| MR-10 | Vulnerable `xlsx` 0.18.5, redundant libs, Bootstrap + Tailwind both used | Adaptive | Medium |
| MR-11 | Add sales/purchase returns (credit notes) | Enhancement | Medium |
| MR-12 | `views.py` ~1,000 lines, repeated CRUD/permission code | Preventive | Low |
| MR-13 | `update_role_permissions()` not atomic | Preventive | High |

---

### MR-01 — Object-level authorization in user operations (Critical, Corrective)

- **Location:** `backend/inventory/views.py` — `update_user()`, `verify_old_password()`
- **Problem:**
  - `update_user()` uses only `IsAuthenticated`; no check that the caller is the target user or an authorized admin; it also accepts a `role` value and assigns it to the target profile → **privilege escalation**.
  - `verify_old_password()` requires authentication but doesn't check that the requested user ID belongs to the caller (or admin) → one user can test password guesses against another account.
  - (Former MR-01.3 is just the overlap of the two points above; same request.)
- **Fix:**
  - Allow update only if `request.user.id == target.id` or caller is an authorized admin (Owner/role with `users` update permission).
  - Role changes only by authorized admins; non-admin supplying `role` must be rejected (403) or ignored.
  - `verify_old_password` only for the account owner (or explicit admin workflow).
  - Return 403 on violations.
- **Tests:** cross-account update rejected; role change by non-admin rejected; own-profile update still works; admin update works; password verify own OK / other's forbidden; login & user-management regression.
- **Risk:** too-strict rules may block legitimate admin workflows — check the frontend user-management/profile screens.

### MR-02 — Transactions endpoint lacks permission (Critical, Corrective)

- **Location:** `get_all_transactions` in `views.py`; DRF defaults in `settings.py`
- **Problem:** No permission check and DRF default permission is `AllowAny` → readable without login.
- **Fix:** add the appropriate module permission check (use existing decorators in `permissions.py`); set `REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = ['rest_framework.permissions.IsAuthenticated']`. Explicitly mark truly public endpoints (login, csrf-cookie) with `AllowAny`.
- **Tests:** anonymous → 401/403; authorized user → 200; user without permission → 403; login and csrf-cookie still work anonymously.

### MR-03 — Sale edit/delete doesn't restore stock (Critical, Corrective)

- **Location:** `models.py` `SaleItem.save()`; sale update/delete flow in serializers/views
- **Problem:** Editing/deleting a sale bulk-deletes and recreates items without restoring stock; update isn't in a transaction; `SaleItem.save()` accesses related product/unit directly (missing-data errors possible).
- **Fix:** on sale update/delete, restore stock for old items first (respecting unit/sub_unit `conversion_factor` exactly as `save()` does), then apply new items; wrap whole operation in `transaction.atomic()`; handle insufficient stock with a validation error and full rollback; also handle single SaleItem delete (signal or explicit logic).
- **Tests:** create; increase qty; decrease qty; delete sale; delete item; insufficient stock; missing related record; rollback after simulated failure leaves stock unchanged.

### MR-04 — Insecure production settings (High, Adaptive)

- **Location:** `settings.py`
- **Problem:** `DEBUG=True`, empty `ALLOWED_HOSTS`, secure cookie flags off, leftover `'POKE'` in CORS methods.
- **Fix:** read `DEBUG`, `ALLOWED_HOSTS`, `SECRET_KEY`, CORS/CSRF origins from env via python-decouple (safe dev defaults kept); `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` driven by `not DEBUG`; remove `POKE`; keep dev workflow working.
- **Tests:** settings check with production env (`DEBUG=False`) → flags on, hosts set; dev still runs.

### MR-05 — Stock race condition (High, Corrective)

- **Problem:** stock updated via read-modify-write on `stock_quantity` → concurrent sales can oversell.
- **Fix:** use `F()` expressions and/or `select_for_update()` inside `transaction.atomic()` for sales, purchases, damaged stock, adjustments (coordinate with MR-03).
- **Tests:** two sales cannot exceed stock (threaded/transactional test; note SQLite limits — document how it was tested); stock never negative.

### MR-06 — No automated tests (High, Preventive) — DO FIRST

- **Problem:** `tests.py` empty.
- **Fix:** create baseline tests (prefer a `tests/` package) for: login/logout/me, permissions per role, products CRUD & stock, sales create/update/delete, purchases & stock updates, dashboard totals, reports sanity, API response formats. Run **before** any change to capture baseline; keep them as regression suite. Tests for known bugs may be written as expected-to-fail/then fixed in the relevant MR.
- **Done when:** `python manage.py test` runs green at the end.

### MR-07 — Damaged stock not audit-logged (Medium, Corrective)

- **Problem:** creating DamagedStock writes no `Activity` entry, contradicting README's "full audit trail".
- **Fix:** create an `Activity` (user, action text consistent with existing entries) when damaged stock is added (follow how other modules log).
- **Tests:** Activity exists after creation with correct user/action.

### MR-08 — Performance (Medium, Perfective)

- **Location:** list endpoints, transactions endpoint, `get_dashboard_data()`
- **Problem:** no pagination; some views skip `select_related`/`prefetch_related` (N+1); transactions merged & sorted in Python; dashboard runs separate sale/payment aggregate queries per customer.
- **Fix:** add `select_related/prefetch_related`; add pagination **without breaking the frontend contract** (prefer opt-in via query params, or update frontend services accordingly and document); replace per-customer loops in dashboard with grouped `annotate/Sum` queries; DB-level ordering/merging where feasible.
- **Tests:** dashboard totals and outstanding balances identical before/after on sample data; empty dataset OK; measure query count (`assertNumQueries` / `CaptureQueriesContext`) and response time before/after.

### MR-09 — README & setup files (Medium, Preventive)

- **Problem:** README says SimpleJWT & SQLite; code uses session auth and env-configured DB; no `requirements.txt` or `.env.example`; screenshots are placeholders.
- **Fix:** update README to match reality (session auth + CSRF, env config, actual structure, run steps, how to run tests); generate `requirements.txt`; add `.env.example`; keep a screenshots section with clear instructions/placeholders that don't pretend to be real (agent cannot take real screenshots).
- **Test:** fresh-clone steps work in order.

### MR-10 — Dependencies (Medium, Adaptive)

- **Problem:** `xlsx` 0.18.5 has known vulnerabilities; `exceljs` already covers Excel export; Bootstrap and Tailwind both used.
- **Fix:** remove `xlsx` and migrate all usages to `exceljs` (+ `file-saver`); verify exports still work; choose one CSS framework only if it can be done **without visual regressions** — otherwise document the decision and the justified scope (don't half-migrate).
- **Tests:** build passes (`npm run build`), Excel export produces a valid file, no leftover `xlsx` imports.

### MR-11 — Returns / credit notes (Medium, Enhancement)

- **Problem:** corrections require deleting records.
- **Fix:** add return models (e.g. `SaleReturn/SaleReturnItem`, `PurchaseReturn/PurchaseReturnItem`) + serializers, endpoints (with permissions), Activity logging, and basic frontend UI; returns adjust stock (use `F()`/atomic) and party balances without deleting records. **Requires migration** + data checks. Validate returned qty ≤ originally sold/purchased qty minus already returned.
- **Tests:** return restores/reduces stock correctly; balances adjust; over-return rejected; atomic rollback.

### MR-12 — Split monolithic `views.py` (Low, Preventive)

- **Problem:** ~1,000 lines, repeated CRUD & permission code.
- **Fix:** split into modules (e.g. `views/auth.py`, `users.py`, `roles.py`, `catalog.py`, `sales.py`, `purchases.py`, `stock.py`, `dashboard.py`) or ViewSets, **no behavior change**; keep URL names/paths, status codes and response shapes identical; re-export from `views/__init__.py` if needed.
- **Tests:** full regression suite identical before/after.

### MR-13 — Atomic role-permission updates (High, Preventive)

- **Location:** `update_role_permissions()` in `views.py`
- **Problem:** deletes and recreates role + user permissions through multiple DB operations with no transaction.
- **Fix:** wrap the whole operation in `transaction.atomic()`.
- **Tests:** success; empty permission set; invalid input; simulated mid-operation failure leaves previous permissions intact.

---

## 3. Execution order

1. **MR-06** baseline tests (login, permissions, products, sales, purchases, dashboard)
2. **MR-01, MR-02** close authorization holes
3. **MR-04** production settings
4. **MR-03, MR-05, MR-13** integrity with transactions
5. **MR-07, MR-08, MR-10** audit log, performance, dependencies
6. **MR-09, MR-12, MR-11** docs, refactoring, then new returns feature

## 4. Constraints

- Preserve existing behavior unless the change is the fix itself.
- Avoid schema changes unless needed (only MR-11 needs one → add migration + data checks).
- One commit per MR (isolated), clear commit message with the MR ID.
- Update the change record/report before marking an MR Done.
- Existing API response formats and frontend integration must keep working (or the frontend is updated in the same MR and documented).

## 5. Regression scope (after every change)

Authentication · user & role updates · product stock display · sale creation & quantity changes · purchase stock updates · dashboard totals & customer balances · API response formats.

## 6. Required final deliverable

A file named **`CHANGES_REPORT.md`** in the repo root with, for **every MR**: status, files changed, commit/branch, problem, **Before → After code** (diff blocks), tests added/run and results, risks/limitations. Details are specified in the agent prompt.
