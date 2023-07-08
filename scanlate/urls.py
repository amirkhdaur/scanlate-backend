from django.urls import path, include, re_path

from . import views
from .routers import ScanlateRouter

router = ScanlateRouter()
router.register(r'roles/subroles', views.SubroleViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'titles/chapters/workers', views.WorkerViewSet, basename='worker')
router.register(r'titles/chapters', views.ChapterViewSet, basename='chapter')
router.register(r'titles/workers', views.WorkerTemplateViewSet)
router.register(r'titles', views.TitleViewSet, basename='title')
router.register(r'users', views.UserViewSet)

urlpatterns = [
    re_path(r'healthcheck/?$', views.HealthCheckAPIView.as_view()),

    # Auth
    re_path(r'auth/register/?$', views.UserRegisterAPIView.as_view()),
    re_path(r'auth/login/?$', views.UserLoginAPIView.as_view()),

    # Router
    path('', include(router.urls)),
]
