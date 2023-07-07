from rest_framework import viewsets, status, exceptions, views, mixins, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny

from .serializers import *
from .models import *
from .permissions import IsAdmin, IsRawProvider, IsCurator, IsQualityChecker


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


class UserRegisterAPIView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')

        if not AllowedEmail.objects.filter(email=email).exists():
            return Response({'detail': 'Email is not allowed'}, status=status.HTTP_403_FORBIDDEN)

        user = serializer.save()

        response_serializer = UserTokenSerializer(instance=user)
        return Response(response_serializer.data)


class UserLoginAPIView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data.get('user')

        response_serializer = UserTokenSerializer(instance=user)
        return Response(response_serializer.data)


class AllowedEmailListAPIView(views.APIView):
    permission_classes = [IsAdmin]

    def get(self, request, *args, **kwargs):
        serializer = EmailSerializer(instance=AllowedEmail.objects.all(), many=True)
        return Response(serializer.data)


class AllowEmailAPIView(views.APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        if AllowedEmail.objects.filter(email=email).exists():
            return Response({'detail': 'Email is already allowed'}, status=status.HTTP_409_CONFLICT)

        AllowedEmail.objects.create(email=email)

        return Response({'detail': 'Email successfully allowed'})


class DisallowEmailAPIView(views.APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        if not AllowedEmail.objects.filter(email=email).exists():
            return Response({'detail': 'Email is already disallowed'}, status=status.HTTP_409_CONFLICT)

        AllowedEmail.objects.get(email=email).delete()

        return Response({'detail': 'Email successfully disallowed'})


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    permission_classes = [IsAdmin]
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.action == 'list':
            return TeamListSerializer
        elif self.action == 'retrieve':
            return TeamRetrieveSerializer
        else:
            return TeamSerializer

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
        return Response(response_serializer.data)

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
            return Response({'detail': 'User is already in team'}, status.HTTP_409_CONFLICT)

        team.members.add(user)
        return Response({'detail': 'Successfully added'})


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
            return Response({'detail': 'User is not in team'}, status.HTTP_409_CONFLICT)

        team.members.remove(user)
        return Response({'detail': 'Successfully removed'})


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
        if self.action == 'list':
            return TitleListSerializer
        elif self.action == 'retrieve':
            return TitleRetrieveSerializer
        else:
            return TitleSerializer

    def create(self, request, *args, **kwargs):
        serializer = TitleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.save()

        response_serializer = self.get_serializer(instance=title)

        headers = self.get_success_headers(serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class WorkerTemplateViewSet(mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    queryset = WorkerTemplate.objects.all()
    serializer_class = WorkerTemplateSerializer
    permission_classes = [IsAdmin]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = WorkerTemplateUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = self.get_serializer(instance=instance)
        return Response(response_serializer.data)


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
        elif self.action == 'retrieve':
            return ChapterRetrieveSerializer
        return ChapterSerializer

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
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = ChapterUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = self.get_serializer(instance=instance)
        return Response(response_serializer.data)


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

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = WorkerUpdateSerializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = self.get_serializer(instance=instance)
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'])
    def upload(self, request, *args, **kwargs):
        worker = self.get_object()
        serializer = UrlSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        worker.upload(serializer.validated_data.get('url'))
        return Response({'detail': 'Successfully uploaded'})


# Users
class UserViewSet(mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == 'update':
            return UserUpdateSerializer
        elif self.action == 'retrieve':
            return UserRetrieveSerializer
        else:
            return UserSerializer
