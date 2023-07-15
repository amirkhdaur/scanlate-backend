from rest_framework import serializers
from rest_framework.authtoken.models import Token
from urllib.parse import urlparse

from . import parser
from .models import *


class ScanlateFloatField(serializers.FloatField):
    def to_representation(self, value):
        return f'{value:g}'


class UrlSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)


# User Register
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        return User.objects.create(
            username=validated_data.get('username'),
            password=validated_data.get('password')
        )


class UserRegisterResponseSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


# User Login
class UserLoginSerializer(serializers.Serializer):
    login = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class UserTokenSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password', 'last_login', 'is_admin']

    def get_token(self, obj):
        token, created = Token.objects.get_or_create(user=obj)
        return token.key


# User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UserCurrentSerializer(serializers.ModelSerializer):
    is_curator = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'is_admin', 'is_curator']

    def get_is_curator(self, obj):
        return Role.CURATOR in obj.roles


class UserRetrieveSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'roles', 'username', 'status']

    def get_roles(self, obj):
        roles = []
        for role in obj.roles:
            titles = Title.objects.filter(workers__user=obj, workers__role=role).order_by('name')
            data = {
                'role': role,
                'titles': TitleListSerializer(titles, many=True).data,
                'titles_count': titles.count()
            }
            roles.append(data)
        return roles


class UserDetailRetrieveSerializer(UserRetrieveSerializer):
    discord_id = serializers.CharField()

    class Meta:
        model = User
        fields = ['id', 'roles', 'username', 'status', 'discord_id', 'vk_id', 'balance']


class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'roles', 'discord_id', 'vk_id']


class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']
        extra_kwargs = {'status': {'required': True}}


# Worker Template
class WorkerTemplateSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)

    class Meta:
        model = WorkerTemplate
        exclude = ['title']


class WorkerTemplateNestedSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)

    class Meta:
        model = WorkerTemplate
        exclude = ['title']


class WorkerTemplateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerTemplate
        exclude = ['title', 'role']


# Worker
class WorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        exclude = ['chapter']


class WorkerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ['id', 'role', 'deadline', 'is_done']


class WorkerUpdateSerializer(WorkerTemplateUpdateSerializer):
    class Meta:
        model = Worker
        exclude = ['chapter', 'role', 'upload_time', 'is_done', 'url']


# Title Serializers
class TitleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['id', 'name', 'slug']


class TitleRetrieveSerializer(serializers.ModelSerializer):
    workers = WorkerTemplateNestedSerializer(many=True)

    class Meta:
        model = Title
        fields = ['id', 'name', 'slug', 'is_active', 'type']


class TitleDetailRetrieveSerializer(TitleRetrieveSerializer):
    class Meta:
        model = Title
        fields = ['id', 'name', 'slug', 'is_active', 'type', 'ad_date']


class TitleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['name', 'slug']


class TitleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = '__all__'


class TitleUrlCreateSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)

    def validate_url(self, value):
        parsed_url = urlparse(value)
        if parsed_url.scheme != 'https':
            raise serializers.ValidationError('scheme is not https')
        elif parsed_url.hostname != 'remanga.org':
            raise serializers.ValidationError('hostname is not remanga.org')
        elif parsed_url.path:
            path_elements = parsed_url.path.split('/')
            print(parsed_url.path)
            print(path_elements)
            if len(path_elements) != 3 or path_elements[1] != 'manga':
                raise serializers.ValidationError('url does not lead to the title')
        return value

    def create(self, validated_data):
        title = parser.create_title(validated_data.get('url'))
        return title


# Chapter
class ChapterSerializer(serializers.ModelSerializer):
    chapter = ScanlateFloatField()
    workers = WorkerSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = '__all__'


class ChapterListSerializer(serializers.ModelSerializer):
    chapter = ScanlateFloatField()

    class Meta:
        model = Chapter
        fields = '__all__'


class ChapterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['title', 'tome', 'chapter', 'pages', 'start_date']
        extra_kwargs = {'start_date': {'required': False}}


class ChapterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['tome', 'chapter', 'pages']


# User Chapters
class WorkerUrlSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)

    class Meta:
        model = Worker
        fields = ['user', 'role', 'url']


class UserChaptersSerializer(serializers.ModelSerializer):
    urls = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = ['id', 'role', 'deadline', 'is_done', 'urls']

    def get_urls(self, obj):
        return WorkerUrlSerializer(obj.chapter.workers.filter(role__in=RoleExtra.dependencies[obj.role]),
                                   many=True).data
