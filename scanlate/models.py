from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone

from .managers import UserManager


class TitleManager(models.Manager):
    def create(self, name, slug):
        title = super().create(name=name, slug=slug)
        to_create = [
            WorkerTemplate(title=title, role=role)
            for role in Role.objects.all()
        ]
        WorkerTemplate.objects.bulk_create(to_create)
        return title


class ChapterManager(models.Manager):
    def create(self, title, tome, chapter, pages, url, start_date=None):
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
                subrole=worker.subrole,
                rate=worker.rate,
                is_paid_by_pages=worker.is_paid_by_pages,
                days_for_work=worker.days_for_work
            )
            for worker in title.workers.all()
        ]
        Worker.objects.bulk_create(to_create)

        raw_provider = chapter.workers.get(role__slug='raw-provider')
        raw_provider.url = url
        raw_provider.is_done = True
        raw_provider.save()

        chapter.calculate_deadlines(order=0)
        return chapter


class PaymentManager(models.Manager):
    def create(self, user, amount, payment_type, worker=None):
        if payment_type == 'in':
            user.balance += amount
            user.save()
        elif payment_type == 'out':
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


class Role(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    order = models.PositiveSmallIntegerField(null=True)


class Subrole(models.Model):
    role = models.ForeignKey(Role, related_name='subroles', on_delete=models.CASCADE)
    name = models.CharField(max_length=150)


class User(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True, validators=[UnicodeUsernameValidator])
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=300)
    is_admin = models.BooleanField(default=False)
    roles = models.ManyToManyField(Role, blank=True)
    subroles = models.ManyToManyField(Subrole, blank=True)
    balance = models.IntegerField(default=0)
    discord_user_id = models.PositiveBigIntegerField()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    objects = UserManager()


class Title(models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)

    is_active = models.BooleanField(default=True)
    ad_date = models.DateField(null=True, default=None)

    objects = TitleManager()


class Chapter(models.Model):
    title = models.ForeignKey(Title, related_name='chapters', on_delete=models.CASCADE)

    tome = models.IntegerField()
    chapter = models.FloatField()
    pages = models.IntegerField()

    start_date = models.DateField()
    end_date = models.DateField(null=True)

    objects = ChapterManager()

    def calculate_deadlines(self, order: int):
        if order == 0:
            date = self.start_date - timezone.timedelta(days=1)
        else:
            upload_time = self.workers.filter(role__order=order-1).order_by('-upload_time').first().upload_time
            date = timezone.localdate(upload_time)

        for worker in self.workers.filter(role__order=order).all():
            worker.deadline = date + timezone.timedelta(days=worker.days_for_work)
            worker.save()

    def end(self):
        self.end_date = timezone.localdate()
        self.save()

        curator = self.workers.get(role__slug='curator')
        curator.is_done = True
        curator.save()

        team = self.title.team
        for worker in self.workers.all():
            team.create_payment(user=worker.user, amount=worker
                                )


class WorkerTemplate(models.Model):
    title = models.ForeignKey(Title, related_name='workers', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, default=None, on_delete=models.CASCADE)

    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    subrole = models.ForeignKey(Subrole, null=True, default=None, on_delete=models.SET_NULL)

    rate = models.IntegerField(default=100)
    is_paid_by_pages = models.BooleanField(default=False)

    days_for_work = models.IntegerField(default=2)


class Worker(models.Model):
    chapter = models.ForeignKey(Chapter, related_name='workers', on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    subrole = models.ForeignKey(Subrole, null=True, on_delete=models.SET_NULL)

    rate = models.IntegerField(default=100)
    is_paid_by_pages = models.BooleanField()

    days_for_work = models.IntegerField()

    deadline = models.DateField(null=True)
    upload_time = models.DateTimeField(null=True)
    url = models.URLField(null=True)
    is_done = models.BooleanField(default=False)

    def upload(self, url):
        self.upload_time = timezone.localtime()
        self.url = url
        self.is_done = True
        self.save()

        if self.role.slug == 'quality-checker':
            self.chapter.end()
        elif not self.chapter.workers.filter(role__order=self.role.order, is_done=False).exists():
            self.chapter.calculate_deadlines(self.role.order + 1)


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
    datetime = models.DateTimeField()
    type = models.CharField(max_length=3)
    worker = models.ForeignKey(Worker, null=True, default=None, on_delete=models.SET_NULL)

    objects = PaymentManager()
