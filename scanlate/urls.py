from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
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
    path('auth/register/', views.UserRegisterAPIView.as_view()),
    path('auth/login/', views.UserLoginAPIView.as_view()),

    # Allow/Disallow Email
    path('auth/allowed-emails/', views.AllowedEmailListAPIView.as_view()),
    path('auth/allowed-emails/allow/', views.AllowEmailAPIView.as_view()),
    path('auth/allowed-emails/disallow/', views.DisallowEmailAPIView.as_view()),

    path('teams/<slug:slug>/members/add/', views.TeamAddMemberAPIView.as_view()),
    path('teams/<slug:slug>/members/remove/', views.TeamRemoveMemberAPIView.as_view()),

    # Router
    path('', include(router.urls)),
]
