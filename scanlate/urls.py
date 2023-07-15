from django.urls import path, include, re_path

from . import views
from .routers import ScanlateRouter

router = ScanlateRouter()
router.register(r'titles/chapters/workers', views.WorkerViewSet)
router.register(r'titles/chapters', views.ChapterViewSet)
router.register(r'titles/workers', views.WorkerTemplateViewSet)
router.register(r'titles', views.TitleViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    re_path(r'healthcheck/?$', views.HealthCheckAPIView.as_view()),

    # Auth
    re_path(r'auth/register/?$', views.UserRegisterAPIView.as_view()),
    re_path(r'auth/login/?$', views.UserLoginAPIView.as_view()),
    re_path(r'auth/change-password/?$', views.UserChangePassword.as_view()),

    # Chapters
    re_path(r'chapters/?$', views.UserChapters.as_view()),

    # Router
    path('', include(router.urls)),
]
