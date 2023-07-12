from rest_framework.filters import BaseFilterBackend
from django.utils import timezone

from .models import Role


def query_param_to_bool(query_param):
    if query_param is None:
        return None
    return query_param.isdigit() and bool(int(query_param))


class TitleFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view.action == 'list':
            return queryset.order_by('name')
        return queryset


class ChapterFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view.action == 'list':
            title_id = request.query_params.get('title_id')
            queryset = queryset.filter(title_id=title_id)

            reverse = query_param_to_bool(request.query_params.get('reverse'))
            if reverse:
                queryset = queryset.order_by('tome', 'chapter')
            else:
                queryset = queryset.order_by('-tome', '-chapter')

            return queryset
        return queryset
