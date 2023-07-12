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


class WorkerFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        if view.action == 'list':
            user_id = request.query_params.get('user_id')
            if user_id:
                queryset = queryset.filter(user_id=user_id).exclude(deadline=None)

                is_done = query_param_to_bool(request.query_params.get('is_done'))
                is_overdue = query_param_to_bool(request.query_params.get('is_overdue'))

                if is_done is not None:
                    queryset = queryset.filter(is_done=is_done)
                elif is_overdue is not None:
                    queryset = queryset.filter(deadline__lt=timezone.localdate())
                else:
                    queryset = queryset.filter(is_done=False)

                return queryset
            else:
                return []
        else:
            return queryset
