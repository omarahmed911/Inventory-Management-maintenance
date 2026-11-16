from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Subquery, OuterRef
from django.db.models.functions import Coalesce
from decimal import Decimal

from ..permissions import permission_required, permission_required_any
from ..models import Category, Unit, Party, Product, PurchaseItem, SaleItem, Activity
from ..serializers import CategorySerializer, UnitSerializer, PartySerializer, ProductSerializer
from .pagination import paginate_if_requested


# CATEGORIES

@api_view(['GET'])
@permission_required("categories", "view")
def get_categories(request):
    categories = Category.objects.all().order_by('-created_at')
    serializer = CategorySerializer(categories, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_required("categories", "view")
def get_category(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = CategorySerializer(category)
    return Response(serializer.data)


@api_view(['POST'])
@permission_required("categories", "create")
def create_category(request):
    serializer = CategorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    category = serializer.save()
    Activity.objects.create(action=f"Create Category: {category.name}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_required("categories", "update")
def update_category(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = CategorySerializer(category, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    Activity.objects.create(action=f"Update Category: {category.name}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_required("categories", "delete")
def delete_category(request, pk):
    try:
        category = Category.objects.get(pk=pk)
        name = category.name
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
    category.delete()
    Activity.objects.create(action=f"Delete Category: {name}", user=request.user if request.user.is_authenticated else None)
    return Response(status=status.HTTP_204_NO_CONTENT)


# UNITS

@api_view(['GET'])
@permission_required("units", "view")
def get_units(request):
    units = Unit.objects.all().order_by('-created_at')
    serializer = UnitSerializer(units, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_required("units", "view")
def get_unit(request, pk):
    try:
        unit = Unit.objects.get(pk=pk)
    except Unit.DoesNotExist:
        return Response({"error": "Unit not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = UnitSerializer(unit)
    return Response(serializer.data)


@api_view(['POST'])
@permission_required("units", "create")
def create_unit(request):
    serializer = UnitSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    unit = serializer.save()
    Activity.objects.create(action=f"Create Unit: {unit.name}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_required("units", "update")
def update_unit(request, pk):
    try:
        unit = Unit.objects.get(pk=pk)
    except Unit.DoesNotExist:
        return Response({"error": "Unit not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = UnitSerializer(unit, data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    Activity.objects.create(action=f"Update Unit: {unit.name}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_required("units", "delete")
def delete_unit(request, pk):
    try:
        unit = Unit.objects.get(pk=pk)
        name = unit.name
    except Unit.DoesNotExist:
        return Response({"error": "Unit not found"}, status=status.HTTP_404_NOT_FOUND)
    unit.delete()
    Activity.objects.create(action=f"Delete Unit: {name}", user=request.user if request.user.is_authenticated else None)
    return Response(status=status.HTTP_204_NO_CONTENT)


# PARTIES

@api_view(['GET'])
@permission_required("parties", "view")
def get_parties(request):
    party_type = request.GET.get("type")
    parties = Party.objects.all()

    if party_type:
        parties = parties.filter(party_type=party_type)

    parties = parties.order_by('-created_at')
    serializer = PartySerializer(parties, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_required("parties", "view")
def get_party(request, pk):
    try:
        party = Party.objects.get(pk=pk)
    except Party.DoesNotExist:
        return Response({"error": "Party not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = PartySerializer(party)
    return Response(serializer.data)


@api_view(['POST'])
@permission_required("parties", "create")
def create_party(request):
    serializer = PartySerializer(data=request.data)
    if serializer.is_valid():
        party = serializer.save()
        Activity.objects.create(action=f"Create Party: {party.name}", user=request.user if request.user.is_authenticated else None)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_required("parties", "update")
def update_party(request, pk):
    try:
        party = Party.objects.get(pk=pk)
    except Party.DoesNotExist:
        return Response({"error": "Party not found"}, status=status.HTTP_404_NOT_FOUND)
    serializer = PartySerializer(party, data=request.data)
    if serializer.is_valid():
        serializer.save()
        Activity.objects.create(action=f"Update Party: {party.name}", user=request.user if request.user.is_authenticated else None)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_required("parties", "delete")
def delete_party(request, pk):
    try:
        party = Party.objects.get(pk=pk)
        name = party.name
    except Party.DoesNotExist:
        return Response({"error": "Party not found"}, status=status.HTTP_404_NOT_FOUND)

    party.delete()
    Activity.objects.create(action=f"Delete Party: {name}", user=request.user if request.user.is_authenticated else None)
    return Response(status=status.HTTP_204_NO_CONTENT)


# PRODUCTS

@api_view(['GET'])
@permission_required_any([("products", "view"), ("sales", "view"), ("sales", "create"), ("purchases", "view"), ("purchases", "create")])
def get_products(request):
    supplier_id = request.GET.get("supplier")
    purchase_subquery = PurchaseItem.objects.filter(product=OuterRef('pk')).values('product').annotate(t=Sum('quantity')).values('t')
    sale_subquery = SaleItem.objects.filter(product=OuterRef('pk')).values('product').annotate(t=Sum('quantity')).values('t')

    products = Product.objects.select_related('category', 'unit', 'sub_unit', 'supplier').annotate(
        total_purchased_val=Coalesce(Subquery(purchase_subquery), Decimal('0.00')),
        total_sold_val=Coalesce(Subquery(sale_subquery), Decimal('0.00'))
    )

    if supplier_id:
        products = products.filter(supplier_id=supplier_id)

    products = products.order_by('-created_at')
    return paginate_if_requested(products, request, ProductSerializer, context={'request': request})


@api_view(['GET'])
@permission_required("products", "view")
def get_product(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProductSerializer(
        product,
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['POST'])
@permission_required("products", "create")
def create_product(request):
    serializer = ProductSerializer(
        data=request.data,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    product = serializer.save()
    Activity.objects.create(action=f"Create Product: {product.product_name}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PUT'])
@permission_required("products", "update")
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.FILES.get('image'):
        if product.image:
            product.image.delete(save=False)

    serializer = ProductSerializer(
        product,
        data=request.data,
        partial=True,
        context={'request': request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    Activity.objects.create(action=f"Update Product: {product.product_name}", user=request.user if request.user.is_authenticated else None)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_required("products", "delete")
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.product_name
    if product.image:
        product.image.delete(save=False)

    product.delete()
    Activity.objects.create(action=f"Delete Product: {name}", user=request.user if request.user.is_authenticated else None)
    return Response(status=status.HTTP_204_NO_CONTENT)
