from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from ..permissions import permission_required
from ..models import Activity
from ..serializers import DamagedStockSerializer, StockAdjustmentSerializer, ActivitySerializer


@api_view(['POST'])
@permission_required("damaged_stock", "create")
def add_damaged_stock(request):
    serializer = DamagedStockSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    damaged = serializer.save()
    Activity.objects.create(
        action=f"Damaged Stock: {damaged.product.product_name} ({damaged.quantity})",
        user=request.user if request.user.is_authenticated else None
    )
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_required("stock_adjustment", "create")
def adjust_stock(request):
    serializer = StockAdjustmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    adjust = serializer.save()
    Activity.objects.create(action=f"Stock Adjustment: {adjust.product}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_activities(request):
    activities = Activity.objects.all().order_by("-created_at")
    serializer = ActivitySerializer(activities, many=True)
    return Response(serializer.data)
