import math
from collections import OrderedDict

from rest_framework.pagination import BasePagination, _positive_int
from rest_framework.response import Response


class CountPagePagination(BasePagination):
    count_query_param = 'count'
    max_count = 40
    default_count = 20
    page_query_param = 'page'

    def paginate_queryset(self, queryset, request, view=None):
        self.count = self.get_count(request)
        self.total_items = self.get_total_items(queryset)
        self.total_pages = math.ceil(self.total_items / self.count)
        self.page = self.get_page(request)
        self.request = request
        if self.total_items == 0 or self.page > self.total_pages:
            return []
        return list(queryset[(self.page - 1) * self.count:self.page * self.count])

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('errors', {}),
            ('content', data),
            ('props', OrderedDict([
                ('total_items', self.total_items),
                ('total_pages', self.total_pages),
                ('page', self.page),
            ])),
        ]))

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'errors': {
                    'type': 'object',
                },
                'content': schema,
                'props': {
                    'type': 'object',
                    'properties': {
                        'total_items': {
                            'type': 'integer',
                            'example': 123,
                        },
                        'total_pages': {
                            'type': 'integer',
                            'example': 123,
                        },
                        'page': {
                            'type': 'integer',
                            'example': 123,
                        },
                    }
                },
            },
        }

    def get_count(self, request):
        if self.count_query_param:
            try:
                return _positive_int(
                    request.query_params[self.count_query_param],
                    strict=True,
                    cutoff=self.max_count
                )
            except (KeyError, ValueError):
                pass

        return self.default_count

    def get_page(self, request):
        try:
            return _positive_int(
                request.query_params[self.page_query_param],
                strict=True,
            )
        except (KeyError, ValueError):
            return 1

    def get_total_items(self, queryset):
        try:
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)
