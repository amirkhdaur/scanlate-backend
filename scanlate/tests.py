from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from .models import *


class TitleManagerTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Равочник', slug='raw-provider')
        Role.objects.create(name='Куратор', slug='curator')
        Role.objects.create(name='Клинер', slug='cleaner', order=0)
        Role.objects.create(name='Переводчик', slug='translator', order=0)
        Role.objects.create(name='Тайпер', slug='typesetter', order=1)
        Role.objects.create(name='Бета', slug='quality-checker', order=2)

    def test_create_title(self):
        title = Title.objects.create(name='Title', slug='title')

        self.assertIsNotNone(title)
        for role in Role.objects.all():
            self.assertTrue(title.workers.filter(role=role).exists())


class ChapterManagerTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Куратор', slug='curator')
        Role.objects.create(name='Равочник', slug='raw-provider', order=0)
        Role.objects.create(name='Клинер', slug='cleaner', order=1)
        Role.objects.create(name='Переводчик', slug='translator', order=1)
        Role.objects.create(name='Тайпер', slug='typesetter', order=2)
        Role.objects.create(name='Бета', slug='quality-checker', order=3)

        self.title = Title.objects.create(name='Title', slug='title')

    def test_create_chapter(self):
        chapter = Chapter.objects.create(title=self.title, tome=1, chapter=1, pages=10)

        self.assertIsNotNone(chapter)
        self.assertEquals(chapter.start_date, timezone.localdate() + timezone.timedelta(days=1))

    def test_create_chapter_with_start_date(self):
        start_date = timezone.localdate() + timezone.timedelta(days=6)
        chapter = Chapter.objects.create(title=self.title, tome=1, chapter=1, pages=10, start_date=start_date)

        self.assertIsNotNone(chapter)
        self.assertEquals(chapter.start_date, start_date)


class ChapterTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Куратор', slug='curator')
        Role.objects.create(name='Равочник', slug='raw-provider', order=0)
        Role.objects.create(name='Клинер', slug='cleaner', order=1)
        Role.objects.create(name='Переводчик', slug='translator', order=1)
        Role.objects.create(name='Тайпер', slug='typesetter', order=2)
        Role.objects.create(name='Бета', slug='quality-checker', order=3)

        title = Title.objects.create(name='Title', slug='title')
        for index, worker in enumerate(title.workers.all()):
            worker.user = User.objects.create(name=worker.role.slug, username=worker.role.slug,
                                              email=worker.role.slug + '@gmail.com', password='1234',
                                              discord_user_id=1234)
            worker.rate = index * 12
            if index % 2 == 0:
                worker.is_paid_by_pages = True
            worker.save()

        self.chapter = Chapter.objects.create(title=title, chapter=1, tome=1, pages=20)

        self.raw_provider = self.chapter.workers.get(role__slug='raw-provider')
        self.cleaner = self.chapter.workers.get(role__slug='cleaner')
        self.translator = self.chapter.workers.get(role__slug='translator')
        self.typesetter = self.chapter.workers.get(role__slug='typesetter')
        self.quality_checker = self.chapter.workers.get(role__slug='quality-checker')

        self.raw_provider.days_for_work = 1
        self.cleaner.days_for_work = 2
        self.translator.days_for_work = 3
        self.typesetter.days_for_work = 7
        self.quality_checker.days_for_work = 5

        self.raw_provider.save()
        self.cleaner.save()
        self.translator.save()
        self.typesetter.save()
        self.quality_checker.save()

    def test_calculate_deadlines(self):
        # Order 0
        self.chapter.calculate_deadlines(order=0)
        self.raw_provider = self.chapter.workers.get(role__slug='raw-provider')

        self.assertEquals(self.raw_provider.deadline, self.chapter.start_date)
        self.raw_provider.upload_time = datetime.combine(self.raw_provider.deadline, datetime.min.time(),
                                                         tzinfo=timezone.get_current_timezone())
        self.raw_provider.save()

        # Order 1
        self.chapter.calculate_deadlines(order=1)
        self.cleaner = self.chapter.workers.get(role__slug='cleaner')
        self.translator = self.chapter.workers.get(role__slug='translator')

        self.assertEquals(self.translator.deadline, self.chapter.start_date + timezone.timedelta(days=3))
        self.assertEquals(self.cleaner.deadline, self.chapter.start_date + timezone.timedelta(days=2))
        self.translator.upload_time = datetime.combine(self.translator.deadline, datetime.min.time(),
                                                       tzinfo=timezone.get_current_timezone())
        self.cleaner.upload_time = datetime.combine(self.cleaner.deadline, datetime.min.time(),
                                                    tzinfo=timezone.get_current_timezone())
        self.translator.save()
        self.cleaner.save()

        # Order 2
        self.chapter.calculate_deadlines(order=2)
        self.typesetter = self.chapter.workers.get(role__slug='typesetter')

        self.assertEquals(self.typesetter.deadline, self.chapter.start_date + timezone.timedelta(days=10))
        self.typesetter.upload_time = datetime.combine(self.typesetter.deadline, datetime.min.time(),
                                                       tzinfo=timezone.get_current_timezone())
        self.typesetter.save()

        # Order 3
        self.chapter.calculate_deadlines(order=3)
        self.quality_checker = self.chapter.workers.get(role__slug='quality-checker')

        self.assertEquals(self.quality_checker.deadline, self.chapter.start_date + timezone.timedelta(days=15))
        self.quality_checker.upload_time = datetime.combine(self.quality_checker.deadline, datetime.min.time(),
                                                            tzinfo=timezone.get_current_timezone())
        self.quality_checker.save()

    def test_end(self):
        self.chapter.end()
        self.assertEquals(self.chapter.end_date, timezone.localdate())
        curator = self.chapter.workers.get(role__slug='curator')
        self.assertTrue(curator.is_done)

    def test_set_published_status(self):
        url = 'https://docs.google.com/document/u/0/'
        for worker in self.chapter.workers.exclude(role__order=None).order_by('role__order').all():
            worker.upload(url=url)

        self.chapter.set_published_status()
        self.assertTrue(self.chapter.is_published)
        for worker in self.chapter.workers.order_by('role__order').all():
            if worker.is_paid_by_pages:
                balance = worker.rate * self.chapter.pages
            else:
                balance = worker.rate
            self.assertEquals(worker.user.balance, balance)


class WorkerTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Куратор', slug='curator')
        Role.objects.create(name='Равочник', slug='raw-provider', order=0)
        Role.objects.create(name='Клинер', slug='cleaner', order=1)
        Role.objects.create(name='Переводчик', slug='translator', order=1)
        Role.objects.create(name='Тайпер', slug='typesetter', order=2)
        Role.objects.create(name='Бета', slug='quality-checker', order=3)

        title = Title.objects.create(name='Title', slug='title')
        self.chapter = Chapter.objects.create(title=title, chapter=1, tome=1, pages=20)

    def test_upload(self):
        url = 'https://docs.google.com/document/u/0/'
        max_order = Role.objects.exclude(order=None).order_by('-order').first().order
        for order in range(max_order + 1):
            for worker in self.chapter.workers.filter(role__order=order):
                worker.upload(url=url)
                self.assertEquals(worker.upload_time.replace(second=0, microsecond=0),
                                  timezone.localtime().replace(second=0, microsecond=0))
                self.assertEquals(worker.url, url)
                self.assertTrue(worker.is_done)
        self.assertIsNotNone(self.chapter.end_date)
