from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class OptionalPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


def paginate_if_requested(queryset, request, serializer_class, context=None):
    if 'page' in request.GET:
        paginator = OptionalPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = serializer_class(page, many=True, context=context or {'request': request})
        return paginator.get_paginated_response(serializer.data)
    serializer = serializer_class(queryset, many=True, context=context or {'request': request})
    return Response(serializer.data)
