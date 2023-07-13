from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import *


class ScanlateFloatField(serializers.FloatField):
    def to_representation(self, value):
        return f'{value:g}'


class UrlSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)


# Subrole
class SubroleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subrole
        fields = '__all__'


class SubroleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subrole
        exclude = ['role']


class SubroleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subrole
        exclude = ['role']


# Role
class RoleSerializer(serializers.ModelSerializer):
    subroles = SubroleNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'subroles']


class RoleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']


# Status
class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ['id', 'name']


# User Register
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'password']


class UserRegisterResponseSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField()


# User Login
class UserLoginSerializer(serializers.Serializer):
    login = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class UserTokenSerializer(serializers.ModelSerializer):
    roles = RoleNestedSerializer(many=True, read_only=True)
    subroles = SubroleNestedSerializer(many=True, read_only=True)
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
        fields = ['id', 'username', 'email', '']


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
        return bool(obj.roles.filter(slug='curator').exists())


class UserRetrieveSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'roles', 'username', 'status']

    def get_roles(self, obj):
        roles = []
        for role in obj.roles.all():
            data = RoleNestedSerializer(role).data
            titles = Title.objects.filter(workers__user=obj, workers__role=role).order_by('name')
            data['titles'] = TitleListSerializer(titles, many=True).data
            data['titles_count'] = titles.count()
            roles.append(data)
        return roles


class UserDetailRetrieveSerializer(UserRetrieveSerializer):
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
        fields = ['name', 'roles', 'subroles', 'discord_id', 'vk_id']


class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['status']
        extra_kwargs = {'status': {'required': True}}


# Worker Template
class WorkerTemplateSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)
    role = RoleNestedSerializer(read_only=True)
    subrole = SubroleNestedSerializer(read_only=True)

    class Meta:
        model = WorkerTemplate
        exclude = ['title']


class WorkerTemplateNestedSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)
    role = RoleNestedSerializer(read_only=True)
    subrole = SubroleNestedSerializer(read_only=True)

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
    role = RoleNestedSerializer(read_only=True)

    class Meta:
        model = Worker
        fields = ['id', 'role', 'deadline', 'is_done']


class WorkerUpdateSerializer(WorkerTemplateUpdateSerializer):
    class Meta:
        model = Worker
        exclude = ['chapter', 'role', 'upload_time', 'is_done', 'url']


# Title Serializers
class TitleSerializer(serializers.ModelSerializer):
    workers = WorkerTemplateNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Title
        fields = '__all__'


class TitleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['id', 'name', 'slug']


class TitleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['name', 'slug']

    def create(self, validated_data):
        return Title.objects.create(
            name=validated_data.get('name'),
            slug=validated_data.get('slug')
        )


class TitleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = '__all__'


class TitleAnySerializer(serializers.ModelSerializer):
    workers = WorkerTemplateNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Title
        fields = ['id', 'name', 'slug', 'is_active']


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

    def create(self, validated_data):
        return Chapter.objects.create(
            title=validated_data.get('title'),
            tome=validated_data.get('tome'),
            chapter=validated_data.get('chapter'),
            pages=validated_data.get('pages'),
            start_date=validated_data.get('start_date')
        )


class ChapterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['tome', 'chapter', 'pages']


# User Chapters
class WorkerUrlSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)
    role = RoleNestedSerializer(read_only=True)

    class Meta:
        model = Worker
        fields = ['user', 'role', 'url']


class UserChaptersSerializer(serializers.ModelSerializer):
    role = RoleNestedSerializer(read_only=True)
    urls = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = ['id', 'role', 'deadline', 'is_done', 'urls']

    def get_urls(self, obj):
        return WorkerUrlSerializer(obj.chapter.workers.filter(role__order=obj.role.order-1), many=True).data
