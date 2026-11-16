from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from ..permissions import permission_required
from ..models import Purchase, Activity
from ..serializers import PurchaseSerializer
from .pagination import paginate_if_requested


@api_view(['GET'])
@permission_required("purchases", "view")
def get_purchases(request):
    purchases = Purchase.objects.select_related('supplier').prefetch_related('items__product__unit', 'items__product__sub_unit').order_by('-created_at')
    return paginate_if_requested(purchases, request, PurchaseSerializer)


@api_view(['GET'])
@permission_required("purchases", "view")
def get_purchase(request, pk):
    try:
        purchase = Purchase.objects.get(pk=pk)
    except Purchase.DoesNotExist:
        return Response({"error": "Purchase not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = PurchaseSerializer(purchase)
    return Response(serializer.data)


@api_view(['POST'])
@permission_required("purchases", "create")
def create_purchase(request):
    serializer = PurchaseSerializer(data=request.data)
    if serializer.is_valid():
        purchase = serializer.save()
        Activity.objects.create(action=f"Create Purchase: {purchase.purchase_no}", user=request.user if request.user.is_authenticated else None)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
