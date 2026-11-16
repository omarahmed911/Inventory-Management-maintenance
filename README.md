# 📦 Inventory Management System

A full-stack **Inventory Management System** built with **Django REST Framework** (backend) and **React + Vite** (frontend). Designed to help businesses manage products, sales, purchases, parties (customers & suppliers), payments, and user roles — all from a clean, responsive UI.

---

## 🚀 Features

- 🔐 **Authentication & Role-Based Access Control** — Owner, Manager, Supervisor, Employee roles with granular module permissions
- 📊 **Dashboard** — Sales, purchases, stock summary with interactive charts (Recharts)
- 🛒 **Product Management** — Categories, units (integer/decimal), stock tracking, product images, sub-unit conversion
- 🤝 **Party Management** — Customers and Suppliers with contact details
- 📥 **Purchase Management** — Record purchases with due/paid amount tracking
- 📤 **Sales Management** — Invoice generation, sale items, per-item pricing, atomic stock adjustments
- 💳 **Payment Tracking** — Payment history with transaction summaries
- 🏭 **Damaged Stock** — Track damaged inventory with full audit logging
- 📋 **Activity Log** — Full audit trail of all user actions
- 📈 **Reports** — Comprehensive reports with Excel export via ExcelJS + file-saver
- 🔑 **User Management** — Object-level authorization, manage user roles, and module permissions
- 🔄 **Password Change Requests** — Workflow for password reset requests

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python / Django | Core framework |
| Django REST Framework | REST API |
| Session Authentication + CSRF | Secure authentication |
| SQLite (default) / Configurable DB | Database via Django ORM |
| python-decouple | Environment configuration |

### Frontend
| Technology | Purpose |
|---|---|
| React 19 | UI Library |
| Vite | Build tool |
| React Router v7 | Routing |
| Axios | HTTP client (with credentials & CSRF) |
| Bootstrap 5 + React-Bootstrap | UI components |
| Tailwind CSS | Utility styling |
| Recharts | Charts & graphs |
| ExcelJS + file-saver | Secure Excel export (no vulnerable dependencies) |

---

## 📁 Project Structure

```
Inventory-Management/
├── backend/
│   ├── inventory/           # Main Django app
│   │   ├── models.py        # Database models (Product, Sale, Purchase, Party...)
│   │   ├── views.py         # API views (split into domain views)
│   │   ├── serializers.py   # DRF serializers
│   │   ├── urls.py          # API routes
│   │   ├── permissions.py   # Custom role/permission decorators
│   │   ├── views_reports.py # Report generation endpoints
│   │   └── tests/           # Automated test suite
│   ├── inventory_system/    # Django project configuration
│   │   ├── settings.py      # Production-ready environment settings
│   │   └── urls.py          # Root URL routing
│   ├── requirements.txt     # Python backend dependencies
│   └── .env.example         # Environment template
└── frontend/
    ├── package.json         # Frontend dependencies
    └── src/
        ├── api/             # Axios API service clients
        ├── components/      # Reusable UI components
        ├── context/         # Auth & Toast contexts
        ├── layouts/         # Sidebar, Topbar, MainLayout
        ├── pages/           # Application views (Dashboard, Products, Sales...)
        └── routes/          # Protected and public routes
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env to set your SECRET_KEY and ALLOWED_HOSTS if needed

# Run migrations
python manage.py migrate

# Create initial admin/owner user
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

The backend API will run at `http://localhost:8000/api/`.

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start development server
npm run dev
```

The frontend will run at `http://localhost:5173`.

---

## 🧪 Running Tests

To run the full backend automated test suite:

```bash
cd backend
python manage.py test inventory.tests
```

To run with existing database preserving speed:

```bash
python manage.py test inventory.tests --keepdb
```

---

## 🔑 Default Roles & Access Control

| Role | Access Level |
|---|---|
| **Owner** | Full administrative access to all modules, roles, and settings |
| **Manager** | Manage inventory, sales, purchases, parties, units, categories |
| **Supervisor** | View and create products, sales, damaged stock, adjustments |
| **Employee** | Sales creation and current stock visibility |

---

## 📸 Screenshots

> Note: To capture live screenshots, start both backend and frontend servers and navigate to the application views:
> - Dashboard: `http://localhost:5173/dashboard`
> - Products: `http://localhost:5173/products`
> - Sales: `http://localhost:5173/sales`

*(Place screenshots in a `screenshots/` directory)*

---

## 📄 License

This project is licensed under the MIT License.
