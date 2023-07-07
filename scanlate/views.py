from rest_framework import viewsets, status, exceptions, views, mixins, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny

from .serializers import *
from .models import *
from .permissions import IsAdmin, IsRawProvider, IsCurator, IsQualityChecker
from .response import ScanlateResponse
from .pagination import CountPagePagination


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


class UserRegisterAPIView(views.APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')

        if not AllowedEmail.objects.filter(email=email).exists():
            return ScanlateResponse(msg='Email is not allowed', status=status.HTTP_403_FORBIDDEN)

        user = serializer.save()

        response_serializer = UserTokenSerializer(instance=user)
        return ScanlateResponse(content=response_serializer.data)


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
            return ScanlateResponse(msg='Invalid username or password', status=status.HTTP_400_BAD_REQUEST)

        response_serializer = UserTokenSerializer(instance=user)
        return ScanlateResponse(content=response_serializer.data)


class AllowedEmailListAPIView(views.APIView):
    permission_classes = [IsAdmin]

    def get(self, request, *args, **kwargs):
        paginator = CountPagePagination()
        result_page = paginator.paginate_queryset(AllowedEmail.objects.all(), request)

        serializer = EmailSerializer(instance=result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AllowEmailAPIView(views.APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        if AllowedEmail.objects.filter(email=email).exists():
            return ScanlateResponse(msg='Email is already allowed', status=status.HTTP_409_CONFLICT)

        AllowedEmail.objects.create(email=email)

        return ScanlateResponse(msg='Email successfully allowed')


class DisallowEmailAPIView(views.APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        if not AllowedEmail.objects.filter(email=email).exists():
            return ScanlateResponse(msg='Email is already disallowed', status=status.HTTP_409_CONFLICT)

        AllowedEmail.objects.get(email=email).delete()

        return ScanlateResponse(msg='Email successfully disallowed')


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    permission_classes = [IsAdmin]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return TeamListSerializer
        else:
            return TeamSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ScanlateResponse(content=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = TeamCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = serializer.save()
        response_serializer = self.get_serializer(instance=team)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TeamUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = self.get_serializer(instance=instance)
        return ScanlateResponse(content=response_serializer.data)

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed(request.method)


class TeamAddMemberAPIView(generics.GenericAPIView):
    queryset = Team.objects.all()
    permission_classes = [IsAdmin]
    lookup_field = 'slug'

    def post(self, request, *args, **kwargs):
        team = self.get_object()
        serializer = UsernameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        if user.teams.filter(pk=team.pk).exists():
            return ScanlateResponse(msg='User is already in team', status=status.HTTP_409_CONFLICT)

        team.members.add(user)
        return ScanlateResponse(msg='Successfully added')


class TeamRemoveMemberAPIView(generics.GenericAPIView):
    queryset = Team.objects.all()
    permission_classes = [IsAdmin]
    lookup_field = 'slug'

    def post(self, request, *args, **kwargs):
        team = self.get_object()
        serializer = UsernameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        if not user.teams.filter(pk=team.pk).exists():
            return ScanlateResponse(msg='User is not in team', status=status.HTTP_409_CONFLICT)

        team.members.remove(user)
        return ScanlateResponse(msg='Successfully removed')


class TitleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]

    def get_queryset(self):
        if self.action == 'list':
            team_id = self.request.query_params.get('team_id')
            try:
                team = Team.objects.get(pk=team_id)
            except Team.DoesNotExist:
                return Team.objects.none()
            return team.titles.all()
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


class ChapterViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]

    def get_queryset(self):
        if self.action == 'list':
            team_id = self.request.query_params.get('title_id')
            try:
                title = Title.objects.get(pk=team_id)
            except Title.DoesNotExist:
                return Title.objects.none()
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

        url_serializer = UrlSerializer(data=dict(url=data.pop('url')))
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


# Users
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
