from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, F
from decimal import Decimal

from ..permissions import permission_required
from ..models import Product, Category, Sale, Purchase, Payment, Party
from ..serializers import DashboardProductSerializer, PaymentSerializer


@api_view(['GET'])
@permission_required("dashboard", "view")
def get_dashboard_data(request):
    from django.db.models import Sum as DSum

    # PRODUCTS
    products = Product.objects.select_related('category', 'unit').all()
    serializer = DashboardProductSerializer(
        products, many=True, context={'request': request}
    )

    # KPI COUNTS
    total_products = products.count()
    low_stock_count = products.filter(stock_quantity__lte=F("minimum_stock")).count()
    category_count = Category.objects.count()

    # SALES
    sales_qs = Sale.objects.select_related('customer', 'worker').order_by('-created_at')
    sales_list = list(sales_qs.values(
        'id', 'invoice_no', 'total_amount', 'payment_mode',
        'created_at', 'customer__name', 'worker__first_name'
    ))
    
    for s in sales_list:
        s['customer_name'] = s.pop('customer__name') or 'Walk-in'
        s['worker_name'] = s.pop('worker__first_name') or ''

    # PURCHASES
    purchases_list = list(
        Purchase.objects.select_related('supplier')
        .order_by('-created_at')
        .values('id', 'purchase_no', 'total_amount', 'paid_amount',
                'due_amount', 'payment_type', 'created_at', 'supplier__name')
    )
    for p in purchases_list:
        p['supplier_name'] = p.pop('supplier__name') or ''

    # PROFIT / LOSS
    total_sales_amt = Sale.objects.aggregate(t=DSum('total_amount'))['t'] or 0
    total_purchase_amt = Purchase.objects.aggregate(t=DSum('total_amount'))['t'] or 0
    profit_loss = {
        "total_sales": total_sales_amt,
        "total_purchase": total_purchase_amt,
        "profit": total_sales_amt - total_purchase_amt,
    }

    # CUSTOMER OUTSTANDING (grouped aggregation)
    customers = Party.objects.filter(party_type="Customer")
    sales_by_customer = {
        row['customer']: row['total']
        for row in Sale.objects.values('customer').annotate(total=DSum('total_amount'))
    }
    payments_by_customer = {
        row['party']: row['total']
        for row in Payment.objects.filter(payment_type="Credit").values('party').annotate(total=DSum('amount'))
    }
    outstanding_list = []
    for c in customers:
        total_bill = sales_by_customer.get(c.id) or 0
        total_paid = payments_by_customer.get(c.id) or 0
        outstanding_list.append({
            "customer_name": c.name,
            "total_bill": total_bill,
            "paid": total_paid,
            "balance": max(total_bill - total_paid, 0),
        })

    # CURRENT STOCK
    stock_list = []
    for p in products:
        stock_list.append({
            "id": p.id,
            "product_name": p.product_name,
            "category": p.category.name if p.category else None,
            "available_quantity": p.stock_quantity,
            "unit": p.unit.short_name if p.unit else None,
            "reorder_level": p.minimum_stock,
            "stock_value": p.stock_quantity * p.cost_price,
        })

    # PARTIES
    parties_list = list(
        Party.objects.values('id', 'name', 'party_type')
    )

    return Response({
        "total_products": total_products,
        "products": serializer.data,
        "low_stock_count": low_stock_count,
        "category_count": category_count,
        "sales": sales_list,
        "purchases": purchases_list,
        "profit_loss": profit_loss,
        "customer_outstanding": outstanding_list,
        "current_stock": stock_list,
        "parties": parties_list,
    })


@api_view(['GET'])
@permission_required("payments", "view")
def get_all_transactions(request):
    transactions = []
    sales_qs = Sale.objects.values(
        'id', 'customer__name', 'total_amount', 'payment_mode', 'invoice_no', 'created_at'
    )
    for s in sales_qs:
        transactions.append({
            "id": f"S-{s['id']}",
            "party_name": s["customer__name"] or "Walk-in",
            "type": "Credit",
            "amount": s["total_amount"],
            "mode": s["payment_mode"] or "Cash",
            "reference": s["invoice_no"],
            "created_at": s["created_at"],
        })

    purchases_qs = Purchase.objects.values(
        'id', 'supplier__name', 'total_amount', 'payment_type', 'purchase_no', 'created_at'
    )
    for p in purchases_qs:
        transactions.append({
            "id": f"P-{p['id']}",
            "party_name": p["supplier__name"] or "",
            "type": "Debit",
            "amount": p["total_amount"],
            "mode": p["payment_type"] or "Cash",
            "reference": p["purchase_no"],
            "created_at": p["created_at"],
        })
    transactions.sort(
        key=lambda x: x["created_at"],
        reverse=True
    )
    return Response(transactions)


@api_view(['GET'])
@permission_required("payments", "view")
def get_payments(request):
    payments = Payment.objects.select_related('party').order_by('-created_at')
    serializer = PaymentSerializer(payments, many=True)
    total_credit = payments.filter(payment_type='Credit').aggregate(total=Sum('amount'))['total'] or 0
    total_debit = payments.filter(payment_type='Debit').aggregate(total=Sum('amount'))['total'] or 0
    data = {"payments": serializer.data, "total_credit": total_credit, "total_debit": total_debit}
    return Response(data)
