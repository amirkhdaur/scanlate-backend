from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import *


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
        fields = '__all__'


class RoleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']


# User Register
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'password', 'discord_user_id']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            name=validated_data.get('name'),
            password=validated_data.get('password'),
            discord_user_id=validated_data.get('discord_user_id'),
        )
        return user


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
    roles = RoleNestedSerializer(many=True, read_only=True)
    subroles = SubroleNestedSerializer(many=True, read_only=True)
    titles = serializers.SerializerMethodField()

    class Meta:
        model = User
        exclude = ['password', 'last_login', 'is_admin']

    def get_titles(self, obj):
        titles = Title.objects.filter(workers__user=obj).order_by('name')
        return TitleListSerializer(titles, many=True).data


class UserNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'username']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'roles', 'subroles', 'discord_user_id']


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
        fields = '__all__'


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


# Chapter
class ChapterSerializer(serializers.ModelSerializer):
    workers = WorkerSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = '__all__'


class ChapterListSerializer(serializers.ModelSerializer):
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
