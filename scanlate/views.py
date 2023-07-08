from rest_framework import viewsets, status, exceptions, views, mixins, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import *
from .models import *
from .permissions import IsAdmin, IsRawProvider, IsCurator, IsQualityChecker
from .response import ScanlateResponse


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
    permission_classes = [IsAdmin]


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


class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAdmin]
    serializer_class = UserSerializer

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
        serializer = UserSerializer(instance=request.user)
        return ScanlateResponse(content=serializer.data)


class TitleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    lookup_field = 'slug'

    def get_queryset(self):
        if self.action == 'list':
            user_id = self.request.query_params.get('user_id')
            if user_id:
                return Title.objects.filter(workers__user_id=user_id)
        return Title.objects.all()

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
        return ScanlateResponse(content=serializer.data)


class ChapterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]

    def get_queryset(self):
        if self.action == 'list':
            title_id = self.request.query_params.get('title_id')
            try:
                title = Title.objects.get(pk=title_id)
            except Title.DoesNotExist:
                return Chapter.objects.none()
            return title.chapters.all()
        return Chapter.objects.all()

    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'update':
            return ChapterListSerializer
        return ChapterSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ScanlateResponse(content=serializer.data)

    def create(self, request, *args, **kwargs):
        data = request.data

        url_serializer = UrlSerializer(data=dict(url=data.pop('url', None)))
        url_serializer.is_valid(raise_exception=True)
        url = url_serializer.validated_data.get('url')

        serializer = ChapterCreateSerializer(data=data, context=dict(url=url))
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


class WorkerViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.UpdateModelMixin,
                    viewsets.GenericViewSet):
    serializer_class = WorkerSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        if self.action == 'list':
            user_id = self.request.query_params.get('user_id')
            if user_id:
                return Worker.objects.filter(user=user_id)
            else:
                return Worker.objects.none()
        else:
            return Worker.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ScanlateResponse(content=serializer.data)

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
