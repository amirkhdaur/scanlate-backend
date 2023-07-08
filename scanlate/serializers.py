from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from .models import *


class UrlSerializer(serializers.Serializer):
    url = serializers.URLField(required=True)


# Role & Category Serializers
class SubroleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subrole
        fields = '__all__'

    def validate(self, attrs):
        role = attrs.get('role')
        if role.subroles.filter(name=attrs.get('name')).exists():
            raise serializers.ValidationError('This subrole is already exists')
        return attrs


class SubroleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subrole
        exclude = ['role']


class SubroleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subrole
        exclude = ['role']


class RoleSerializer(serializers.ModelSerializer):
    subroles = SubroleNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = '__all__'


class RoleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


# User Related Serializers
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            name=validated_data.get('name'),
            password=validated_data.get('password'),
            discord_user_id=validated_data.get('discord_user_id'),
        )
        return user

    class Meta:
        model = User
        fields = ['username', 'email', 'name', 'password', 'discord_user_id']


class UserLoginSerializer(serializers.Serializer):
    login = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        user = None

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            if user is None:
                raise serializers.ValidationError('No user with this username')

        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    roles = RoleNestedSerializer(many=True, read_only=True)
    subroles = SubroleNestedSerializer(many=True, read_only=True)

    class Meta:
        model = User
        exclude = ['password', 'last_login', 'is_admin']


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


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'roles', 'subroles', 'discord_user_id']


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


# Team Serializers
class TeamSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Team
        fields = '__all__'


class TeamListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        exclude = ['members']


class TeamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'slug']


class TeamUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['name', 'slug']


# Workers Serializers
class WorkerTemplateSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role = RoleNestedSerializer(read_only=True)
    subrole = SubroleNestedSerializer(read_only=True)

    class Meta:
        model = WorkerTemplate
        exclude = ['title']


class WorkerTemplateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerTemplate
        exclude = ['title', 'role']


class WorkerSerializer(WorkerTemplateSerializer):
    class Meta:
        model = Worker
        exclude = ['chapter']


class WorkerUpdateSerializer(WorkerTemplateUpdateSerializer):
    class Meta:
        model = Worker
        exclude = ['chapter', 'role', 'upload_time', 'is_done', 'url']


# Title Serializers
class TitleSerializer(serializers.ModelSerializer):
    workers = WorkerTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = Title
        exclude = ['team']


class TitleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        exclude = ['team']


class TitleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['name', 'slug', 'team']

    def validate(self, attrs):
        team = attrs.get('team')
        if team.titles.filter(slug=attrs.get('slug')).exists():
            raise serializers.ValidationError('Title with this slug is already in team')
        return attrs

    def create(self, validated_data):
        team = validated_data.get('team')
        title = team.create_title(
            name=validated_data.get('name'),
            slug=validated_data.get('slug')
        )
        return title


class TitleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        exclude = ['team']


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
        fields = ['title', 'tome', 'chapter', 'pages']

    def create(self, validated_data):
        title = validated_data.get('title')
        chapter = title.create_chapter(
            tome=validated_data.get('tome'),
            chapter=validated_data.get('chapter'),
            pages=validated_data.get('pages'),
            url=self.context.get('url')
        )
        return chapter


class ChapterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        exclude = ['title', 'start_date', 'end_date']
