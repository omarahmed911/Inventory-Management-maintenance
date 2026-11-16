from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from ..models import SaleReturn, PurchaseReturn, Activity
from ..serializers import SaleReturnSerializer, PurchaseReturnSerializer
from ..permissions import permission_required
from .pagination import OptionalPagination


@api_view(['GET'])
@permission_required("sales", "view")
def get_sale_returns(request):
    returns = SaleReturn.objects.select_related('sale', 'sale__customer').prefetch_related('items__product').order_by('-created_at')
    paginator = OptionalPagination()
    page = paginator.paginate_queryset(returns, request)
    if page is not None:
        serializer = SaleReturnSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = SaleReturnSerializer(returns, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_required("sales", "create")
def create_sale_return(request):
    serializer = SaleReturnSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                sale_return = serializer.save()
                Activity.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action=f"Create Sale Return: {sale_return.return_no}"
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, Exception) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_required("purchases", "view")
def get_purchase_returns(request):
    returns = PurchaseReturn.objects.select_related('purchase', 'purchase__supplier').prefetch_related('items__product').order_by('-created_at')
    paginator = OptionalPagination()
    page = paginator.paginate_queryset(returns, request)
    if page is not None:
        serializer = PurchaseReturnSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    serializer = PurchaseReturnSerializer(returns, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_required("purchases", "create")
def create_purchase_return(request):
    serializer = PurchaseReturnSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                purchase_return = serializer.save()
                Activity.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action=f"Create Purchase Return: {purchase_return.return_no}"
                )
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        except (DjangoValidationError, Exception) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
