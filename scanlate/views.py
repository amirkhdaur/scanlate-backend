from rest_framework import viewsets, status, exceptions, views, mixins, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions

from .serializers import *
from .permissions import *
from .response import ScanlateResponse
from .filters import *
from .models import *


# HealthCheck
class HealthCheckAPIView(views.APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return ScanlateResponse(msg='Good')


# Role & Subrole
class RoleViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [AllowAny]


class SubroleViewSet(mixins.CreateModelMixin,
                     mixins.DestroyModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    queryset = Subrole.objects.all()
    serializer_class = SubroleSerializer
    permission_classes = [IsAdmin]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.validated_data.get('role')

        if role.subroles.filter(name=serializer.validated_data.get('name')).exists():
            return ScanlateResponse(msg='This subrole is already exists', status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        headers = self.get_success_headers(serializer.data)
        return ScanlateResponse(content=serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SubroleUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if instance.role.subroles.filter(name=serializer.validated_data.get('name')).exists():
            return ScanlateResponse(msg='This subrole is already exists', status=status.HTTP_400_BAD_REQUEST)
        instance = serializer.save()

        response_serializer = self.get_serializer(instance=instance)
        return ScanlateResponse(content=response_serializer.data)


# Status
class StatusViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    permission_classes = [AllowAny]


# User
class UserRegisterAPIView(views.APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        password = User.objects.make_random_password()
        request.data['password'] = password
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = {
            'username': user.username,
            'email': user.email,
            'password': password
        }
        return ScanlateResponse(content=data)


class UserLoginAPIView(views.APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        login = serializer.validated_data.get('login').lower()
        password = serializer.validated_data.get('password')

        user = authenticate(username=login, password=password)
        if not user:
            return ScanlateResponse(msg='Invalid login or password', status=status.HTTP_400_BAD_REQUEST)

        response_serializer = UserTokenSerializer(instance=user)
        return ScanlateResponse(content=response_serializer.data)


class UserChangePassword(views.APIView):
    def post(self, request):
        user = request.user
        password = request.data.get('password')

        errors = {}
        try:
            validate_password(password=password, user=user)
        except django_exceptions.ValidationError as e:
            errors['password'] = list(e.messages)

        if errors:
            raise serializers.ValidationError(errors)

        user.set_password(password)
        user.save()
        return ScanlateResponse(msg='Password successfully changed')


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAdmin | IsSafeMethod]

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'update':
            if IsUser().has_object_permission(request=self.request, view=self, obj=self.get_object()) or \
                    IsCurator().has_permission(self.request, self) or \
                    IsAdmin().has_permission(self.request, self):
                return UserDetailRetrieveSerializer
            return UserRetrieveSerializer
        else:
            return UserListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ScanlateResponse(content=serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_serializer = self.get_serializer(user)
        return ScanlateResponse(content=response_serializer.data)

    @action(detail=False, methods=['get'])
    def current(self, request):
        serializer = UserCurrentSerializer(instance=request.user)
        return ScanlateResponse(content=serializer.data)

    @action(detail=True, methods=['put'])
    def status(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserStatusSerializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return ScanlateResponse(content=serializer.data)


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.all()
    permission_classes = [IsAdmin]
    lookup_field = 'slug'
    filter_backends = [TitleFilterBackend]

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'update':
            return TitleListSerializer
        else:
            return TitleSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ScanlateResponse(content=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = TitleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.save()

        response_serializer = self.get_serializer(instance=title)
        headers = self.get_success_headers(serializer.data)
        return ScanlateResponse(content=response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TitleUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = self.get_serializer(instance)
        return ScanlateResponse(content=response_serializer.data)


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all()
    permission_classes = [IsAdmin]
    filter_backends = [ChapterFilterBackend]

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'update':
            return ChapterListSerializer
        return ChapterSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ScanlateResponse(content=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = ChapterCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chapter = serializer.save()

        response_serializer = self.get_serializer(instance=chapter)
        headers = self.get_success_headers(serializer.data)
        return ScanlateResponse(content=response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ChapterUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = self.get_serializer(instance=instance)
        return ScanlateResponse(content=response_serializer.data)


class WorkerViewSet(mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    queryset = Worker.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = WorkerSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = WorkerUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get('user')
        if user and not user.roles.filter(pk=instance.role.pk).exists():
            return ScanlateResponse(msg='User does not have this role', status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        response_serializer = self.get_serializer(instance=instance)
        return ScanlateResponse(content=response_serializer.data)

    @action(detail=True, methods=['post'])
    def upload(self, request, *args, **kwargs):
        worker = self.get_object()
        serializer = UrlSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        worker.upload(serializer.validated_data.get('url'))
        return ScanlateResponse(msg='Successfully uploaded')


class WorkerTemplateViewSet(mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    queryset = WorkerTemplate.objects.all()
    serializer_class = WorkerTemplateSerializer
    permission_classes = [IsAdmin]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = WorkerTemplateUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get('user')
        if user and not user.roles.filter(pk=instance.role.pk).exists():
            return ScanlateResponse(msg='User does not have this role', status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()
        response_serializer = self.get_serializer(instance=instance)
        return ScanlateResponse(content=response_serializer.data)


class UserChapters(views.APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        is_done = query_param_to_bool(request.query_params.get('is_done'))
        queryset = Worker.objects.filter(user=request.user, is_done=bool(is_done)).exclude(deadline=None)
        serializer = UserChaptersSerializer(queryset, many=True)
        return ScanlateResponse(content=serializer.data)
