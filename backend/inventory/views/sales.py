from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

from ..permissions import permission_required
from ..models import Sale, Activity
from ..serializers import SaleSerializer
from .pagination import paginate_if_requested


@api_view(['GET'])
@permission_required("sales", "view")
def get_sales(request):
    sales = Sale.objects.select_related('customer', 'worker').prefetch_related('items__product__unit', 'items__product__sub_unit').order_by('-created_at')
    return paginate_if_requested(sales, request, SaleSerializer)


@api_view(['GET'])
@permission_required("sales", "view")
def get_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    serializer = SaleSerializer(sale)
    return Response(serializer.data)


@api_view(['POST'])
@permission_required("sales", "create")
def create_sale(request):
    serializer = SaleSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    sale = serializer.save()
    Activity.objects.create(action=f"Create Sale: {sale.invoice_no}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_required("sales", "update")
def update_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    serializer = SaleSerializer(sale, data=request.data)
    serializer.is_valid(raise_exception=True)
    sale = serializer.save()
    Activity.objects.create(action=f"Update Sale: {sale.invoice_no}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_required("sales", "delete")
@transaction.atomic
def delete_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    invoice_no = sale.invoice_no
    sale.delete()
    Activity.objects.create(action=f"Delete Sale: {invoice_no}", user=request.user if request.user.is_authenticated else None)
    return Response({"message": "Sale deleted"})
