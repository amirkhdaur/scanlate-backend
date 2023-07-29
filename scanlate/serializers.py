from rest_framework import serializers
from rest_framework.authtoken.models import Token
from urllib.parse import urlparse

from . import parser
from .models import *


class ScanlateFloatField(serializers.FloatField):
    def to_representation(self, value):
        return f'{value:g}'


class UrlSerializer(serializers.Serializer):
    url = serializers.URLField(required=True, allow_blank=True)


# User Current
class UserCurrentSerializer(serializers.ModelSerializer):
    is_curator = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'is_admin', 'is_curator', 'balance']

    def get_is_curator(self, obj):
        return Role.CURATOR in obj.roles


# User Register
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'roles']
        extra_kwargs = {'roles': {'required': True}}

    def create(self, validated_data):
        return User.objects.create(
            username=validated_data.get('username'),
            password=validated_data.get('password'),
            roles=validated_data.get('roles')
        )


class UserRegisterResponseSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


# User Login
class UserLoginSerializer(serializers.Serializer):
    login = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class UserLoginResponseSerializer(UserCurrentSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'is_admin', 'is_curator', 'token', 'balance']

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


class UserRetrieveSerializer(serializers.ModelSerializer):
    discord_id = serializers.CharField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'roles', 'username', 'status', 'discord_id', 'vk_id']

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
        fields = ['roles', 'discord_id', 'vk_id']


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
        fields = ['id', 'user', 'role']


class WorkerTemplateDetailNestedSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)

    class Meta:
        model = WorkerTemplate
        exclude = ['title']


class WorkerTemplateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerTemplate
        exclude = ['title', 'role']


# Worker
class WorkerUpdateSerializer(WorkerTemplateUpdateSerializer):
    class Meta:
        model = Worker
        fields = ['rate', 'is_paid_by_pages', 'days_for_work', 'user']


class WorkerUpdateResponseSerializer(WorkerTemplateUpdateSerializer):
    user = UserNestedSerializer(read_only=True)

    class Meta:
        model = Worker
        exclude = ['chapter']


class WorkerNestedSerializer(WorkerTemplateUpdateSerializer):
    user = UserNestedSerializer(read_only=True)

    class Meta:
        model = Worker
        exclude = ['chapter']


# Title Serializers
class TitleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['id', 'name', 'slug', 'img', 'is_active']


class TitleRetrieveSerializer(serializers.ModelSerializer):
    workers = serializers.SerializerMethodField()

    class Meta:
        model = Title
        fields = ['id', 'name', 'slug', 'is_active', 'raw', 'discord_channel', 'img', 'workers']

    def get_workers(self, title):
        workers = []
        user = self.context.get('user')
        user_workers = title.workers.filter(user=user)
        other_workers = title.workers.exclude(user=user)

        workers.extend(WorkerTemplateNestedSerializer(instance=other_workers, many=True).data)
        workers.extend(WorkerTemplateDetailNestedSerializer(instance=user_workers, many=True).data)
        workers = sorted(workers, key=lambda x: x['role'])
        return workers


class TitleDetailRetrieveSerializer(TitleRetrieveSerializer):
    workers = WorkerTemplateDetailNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Title
        fields = ['id', 'name', 'slug', 'is_active', 'raw', 'discord_channel', 'img', 'ad_date', 'workers']


class TitleWorkerTemplateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerTemplate
        fields = ['role', 'rate', 'is_paid_by_pages', 'user', 'days_for_work']
        extra_kwargs = {
            'rate': {'required': True},
            'is_paid_by_pages': {'required': True},
            'user': {'required': True},
            'days_for_work': {'required': True}
        }


class TitleCreateSerializer(serializers.ModelSerializer):
    workers = TitleWorkerTemplateUpdateSerializer(many=True)

    class Meta:
        model = Title
        fields = ['slug', 'is_active', 'discord_channel', 'raw', 'ad_date', 'workers']

    def validate_workers(self, workers):
        if len(workers) != len(Role.values):
            raise serializers.ValidationError('Здесь меньше или больше необходимых ролей.')
        for role in Role.values:
            role_is_there = False
            for worker in workers:
                if worker.get('role') == role:
                    role_is_there = True
                    break
            if not role_is_there:
                raise serializers.ValidationError(f'Нет роли {role}.')
        return workers

    def create(self, validated_data):
        title_slug = validated_data.pop('slug')
        workers_data = validated_data.pop('workers')
        title = parser.create_title(title_slug=title_slug, **validated_data)
        if title is None:
            raise serializers.ValidationError({'detail': 'Не удалось создать тайтл.'})

        to_create = [
            WorkerTemplate(title=title,
                           role=worker_data.get('role'),
                           rate=worker_data.get('rate'),
                           is_paid_by_pages=worker_data.get('is_paid_by_pages'),
                           user=worker_data.get('user'),
                           days_for_work=worker_data.get('days_for_work'))
            for worker_data in workers_data
        ]
        WorkerTemplate.objects.bulk_create(to_create)
        return title


class TitleUpdateSerializer(serializers.ModelSerializer):
    workers = TitleWorkerTemplateUpdateSerializer(many=True)

    class Meta:
        model = Title
        fields = ['is_active', 'discord_channel', 'raw', 'ad_date', 'workers']

    def validate_workers(self, workers):
        if len(workers) != len(Role.values):
            raise serializers.ValidationError('Здесь меньше или больше необходимых ролей.')
        for role in Role.values:
            role_is_there = False
            for worker in workers:
                if worker.get('role') == role:
                    role_is_there = True
                    break
            if not role_is_there:
                raise serializers.ValidationError(f'Нет роли {role}.')
        return workers

    def update(self, instance, validated_data):
        workers_data = validated_data.pop('workers')
        workers = instance.workers.all()
        for worker in workers:
            worker_data = {}
            for el in workers_data:
                if el.get('role') == worker.role:
                    worker_data = el
                    break
            worker.rate = worker_data.get('rate')
            worker.is_paid_by_pages = worker_data.get('is_paid_by_pages')
            worker.user = worker_data.get('user')
            worker.days_for_work = worker_data.get('days_for_work')
        WorkerTemplate.objects.bulk_update(workers, ['rate', 'is_paid_by_pages', 'user', 'days_for_work'])

        instance.is_active = validated_data.get('is_active')
        instance.ad_date = validated_data.get('ad_date')
        instance.discord_channel = validated_data.get('discord_channel')
        instance.raw = validated_data.get('raw')
        instance.save()
        return instance


class TitleUpdateResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = '__all__'


class TitleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Title
        fields = ['id', 'name', 'slug']


# Chapter
class ChapterRetrieveSerializer(serializers.ModelSerializer):
    chapter = ScanlateFloatField()
    workers = WorkerNestedSerializer(many=True, read_only=True)

    class Meta:
        model = Chapter
        fields = '__all__'


class ChapterListSerializer(serializers.ModelSerializer):
    chapter = ScanlateFloatField()

    class Meta:
        model = Chapter
        fields = '__all__'


class ChapterWorkerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worker
        fields = ['role', 'rate', 'is_paid_by_pages', 'user', 'days_for_work']
        extra_kwargs = {
            'rate': {'required': True},
            'is_paid_by_pages': {'required': True},
            'user': {'required': True},
            'days_for_work': {'required': True}
        }


class ChapterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = ['title', 'tome', 'chapter', 'pages', 'start_date']
        extra_kwargs = {'start_date': {'required': False}}


class ChapterUpdateSerializer(serializers.ModelSerializer):
    workers = ChapterWorkerSerializer(many=True)

    class Meta:
        model = Chapter
        fields = ['tome', 'chapter', 'pages', 'workers']

    def validate_workers(self, workers):
        if len(workers) != len(Role.values):
            raise serializers.ValidationError('Здесь меньше или больше необходимых ролей.')
        for role in Role.values:
            role_is_there = False
            for worker in workers:
                if worker.get('role') == role:
                    role_is_there = True
                    break
            if not role_is_there:
                raise serializers.ValidationError(f'Нет роли {role}.')
        return workers

    def update(self, instance, validated_data):
        workers_data = validated_data.pop('workers')
        workers = instance.workers.all()
        for worker in workers:
            worker_data = {}
            for el in workers_data:
                if el.get('role') == worker.role:
                    worker_data = el
                    break
            worker.rate = worker_data.get('rate')
            worker.is_paid_by_pages = worker_data.get('is_paid_by_pages')
            worker.user = worker_data.get('user')
            worker.days_for_work = worker_data.get('days_for_work')
        Worker.objects.bulk_update(workers, ['rate', 'is_paid_by_pages', 'user', 'days_for_work'])

        instance.tome = validated_data.get('tome')
        instance.chapter = validated_data.get('chapter')
        instance.pages = validated_data.get('pages')
        instance.save()
        return instance


class ChapterUpdateResponseSerializer(serializers.ModelSerializer):
    chapter = ScanlateFloatField()

    class Meta:
        model = Chapter
        fields = '__all__'


class ChapterNestedSerializer(serializers.ModelSerializer):
    chapter = ScanlateFloatField()

    class Meta:
        model = Chapter
        fields = ['id', 'tome', 'chapter']


# User Chapters
class WorkerUrlSerializer(serializers.ModelSerializer):
    user = UserNestedSerializer(read_only=True)

    class Meta:
        model = Worker
        fields = ['user', 'role', 'url']


class UserChaptersSerializer(serializers.ModelSerializer):
    urls = serializers.SerializerMethodField()
    chapter = ChapterNestedSerializer()
    title = serializers.SerializerMethodField()

    class Meta:
        model = Worker
        fields = ['id', 'role', 'deadline', 'is_done', 'urls', 'chapter', 'title']

    def get_urls(self, obj):
        if obj.role == RoleExtra.first_role:
            return []
        return WorkerUrlSerializer(obj.chapter.workers.filter(role__in=RoleExtra.dependencies[obj.role]),
                                   many=True).data

    def get_title(self, obj):
        return TitleNestedSerializer(obj.chapter.title).data
