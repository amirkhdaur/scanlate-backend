from django.urls import path, include, re_path

from . import views
from .routers import ScanlateRouter

router = ScanlateRouter()
router.register(r'teams', views.TeamViewSet)
router.register(r'roles/subroles', views.SubroleViewSet)
router.register(r'roles', views.RoleViewSet)
router.register(r'titles/chapters/workers', views.WorkerViewSet, basename='worker')
router.register(r'titles/chapters', views.ChapterViewSet, basename='chapter')
router.register(r'titles/workers', views.WorkerTemplateViewSet)
router.register(r'titles', views.TitleViewSet, basename='title')
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # Auth
    re_path('auth/register/?$', views.UserRegisterAPIView.as_view()),
    re_path('auth/login/?$', views.UserLoginAPIView.as_view()),

    # Allow/Disallow Email
    re_path('auth/allowed-emails/?$', views.AllowedEmailListAPIView.as_view()),
    re_path('auth/allowed-emails/allow/?$', views.AllowEmailAPIView.as_view()),
    re_path('auth/allowed-emails/disallow/?$', views.DisallowEmailAPIView.as_view()),

    re_path('teams/<slug:slug>/members/add/?$', views.TeamAddMemberAPIView.as_view()),
    re_path('teams/<slug:slug>/members/remove/?$', views.TeamRemoveMemberAPIView.as_view()),

    # Router
    path('', include(router.urls)),
]
