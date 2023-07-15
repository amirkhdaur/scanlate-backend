from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


class Status(models.IntegerChoices):
    MARATHON = 0
    ONGOING = 1
    ENOUGH = 2
    VACATION = 3


class Role(models.IntegerChoices):
    CURATOR = 0
    RAW_PROVIDER = 1
    CLEANER = 2
    TRANSLATOR = 3
    TYPESETTER = 4
    QUALITY_CHECKER = 5


class PaymentType(models.IntegerChoices):
    IN = 0
    OUT = 1


class RoleExtra:
    dependencies = {
        Role.CURATOR: [],
        Role.RAW_PROVIDER: [Role.CURATOR],
        Role.CLEANER: [Role.RAW_PROVIDER],
        Role.TRANSLATOR: [Role.RAW_PROVIDER],
        Role.TYPESETTER: [Role.CLEANER, Role.TRANSLATOR],
        Role.QUALITY_CHECKER: [Role.TYPESETTER]
    }
    continuations = {
        Role.CURATOR: [Role.RAW_PROVIDER],
        Role.RAW_PROVIDER: [Role.TRANSLATOR, Role.CLEANER],
        Role.CLEANER: [Role.TYPESETTER],
        Role.TRANSLATOR: [Role.TYPESETTER],
        Role.TYPESETTER: [Role.QUALITY_CHECKER],
        Role.QUALITY_CHECKER: []
    }
    first_role = Role.RAW_PROVIDER
    last_role = Role.QUALITY_CHECKER


class UserManager(BaseUserManager):
    def create(self, username, password, roles):
        username = AbstractBaseUser.normalize_username(username)
        user = self.model(username=username, roles=roles)
        user.set_password(password)
        user.save()
        return user


class TitleManager(models.Manager):
    def create(self, name, slug):
        title = super().create(name=name, slug=slug)

        to_create = [
            WorkerTemplate(title=title, role=role)
            for role in Role.values
        ]
        WorkerTemplate.objects.bulk_create(to_create)
        return title


class ChapterManager(models.Manager):
    def create(self, title, tome, chapter, pages, start_date=None):
        if start_date is None:
            start_date = timezone.localdate() + timezone.timedelta(days=1)

        chapter = super().create(
            title=title,
            tome=tome,
            chapter=chapter,
            pages=pages,
            start_date=start_date
        )

        to_create = [
            Worker(
                chapter=chapter,
                user=worker.user,
                role=worker.role,
                rate=worker.rate,
                is_paid_by_pages=worker.is_paid_by_pages,
                days_for_work=worker.days_for_work
            )
            for worker in title.workers.all()
        ]
        Worker.objects.bulk_create(to_create)
        chapter.start()
        return chapter


class PaymentManager(models.Manager):
    def create(self, user, amount, payment_type, worker=None):
        if payment_type == PaymentType.IN:
            user.balance += amount
            user.save()
        elif payment_type == PaymentType.OUT:
            user.balance -= amount
            user.save()
        else:
            raise ValueError('payment_type must be "in" or "out"')

        return super().create(
            user=user,
            amount=amount,
            datetime=timezone.localtime(),
            type=payment_type,
            worker=worker
        )


class User(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True, validators=[UnicodeUsernameValidator])
    is_admin = models.BooleanField(default=False)
    roles = ArrayField(models.IntegerField(choices=Role.choices), blank=True, default=list)
    balance = models.IntegerField(default=0)
    discord_id = models.PositiveBigIntegerField(null=True)
    vk_id = models.PositiveBigIntegerField(null=True)
    status = models.IntegerField(null=True, choices=Status.choices)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ['username']


class Title(models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)

    is_active = models.BooleanField(default=True)
    ad_date = models.DateField(null=True, default=None)
    type = models.CharField(blank=True, default='')

    objects = TitleManager()

    class Meta:
        ordering = ['name']


class Chapter(models.Model):
    title = models.ForeignKey(Title, related_name='chapters', on_delete=models.CASCADE)

    tome = models.IntegerField()
    chapter = models.FloatField()
    pages = models.IntegerField()

    start_date = models.DateField()
    end_date = models.DateField(null=True)

    is_published = models.BooleanField(default=False)

    objects = ChapterManager()

    class Meta:
        ordering = ['tome', 'chapter']

    def set_published_status(self):
        if not self.is_published and not self.workers.filter(is_done=False).exists():
            self.is_published = True
            self.save()

            for worker in self.workers.all():
                if worker.is_paid_by_pages:
                    amount = worker.rate * self.pages
                else:
                    amount = worker.rate
                Payment.objects.create(
                    user=worker.user,
                    amount=amount,
                    payment_type=PaymentType.IN,
                    worker=worker
                )

    def calculate_deadline_for_role(self, role, date):
        worker = self.workers.get(role=role)
        worker.deadline = date + timezone.timedelta(days=worker.days_for_work)
        worker.save()

    def calculate_deadlines(self, current_role):
        dependencies = RoleExtra.dependencies
        continuations = RoleExtra.continuations
        first_role = RoleExtra.first_role
        last_role = RoleExtra.last_role

        if current_role == last_role:
            self.end()
            return

        for role in continuations[current_role]:
            if not self.workers.filter(role__in=dependencies[role], is_done=False).exists():
                worker = self.workers.get(role=role)

                if role == first_role:
                    date = self.start_date - timezone.timedelta(days=1)
                else:
                    date = timezone.localdate(self.workers.filter(role__in=dependencies[role])
                                              .aggregate(models.Max('upload_time')).get('upload_time__max'))
                worker.deadline = date + timezone.timedelta(days=worker.days_for_work)
                worker.save()

    def start(self):
        curator = self.workers.get(role=Role.CURATOR)
        curator.is_done = True
        curator.save()
        self.calculate_deadlines(Role.CURATOR)

    def end(self):
        self.end_date = timezone.localdate()
        self.save()


class WorkerTemplate(models.Model):
    title = models.ForeignKey(Title, related_name='workers', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, default=None, on_delete=models.CASCADE)
    role = models.IntegerField(choices=Role.choices)

    rate = models.IntegerField(default=100)
    is_paid_by_pages = models.BooleanField(default=False)

    days_for_work = models.IntegerField(default=2)

    class Meta:
        ordering = ['role']


class Worker(models.Model):
    chapter = models.ForeignKey(Chapter, related_name='workers', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    role = models.IntegerField(choices=Role.choices)

    rate = models.IntegerField(default=100)
    is_paid_by_pages = models.BooleanField()

    days_for_work = models.IntegerField()

    deadline = models.DateField(null=True)
    upload_time = models.DateTimeField(null=True)
    url = models.URLField(null=True, blank=True)
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ['role']

    def upload(self, url):
        self.upload_time = timezone.localtime()
        self.url = url
        self.is_done = True
        self.save()
        self.chapter.calculate_deadlines(self.role)


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    datetime = models.DateTimeField()
    type = models.IntegerField(choices=PaymentType.choices)
    worker = models.ForeignKey(Worker, null=True, default=None, on_delete=models.SET_NULL)

    objects = PaymentManager()
