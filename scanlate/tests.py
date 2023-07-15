from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from .models import *


class TitleManagerTestCase(TestCase):
    def test_create_title(self):
        title = Title.objects.create(name='Title', slug='title')

        self.assertIsNotNone(title)
        for role in Role.values:
            self.assertTrue(title.workers.filter(role=role).exists())


class ChapterManagerTestCase(TestCase):
    def setUp(self):
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
        title = Title.objects.create(name='Title', slug='title')
        for index, worker in enumerate(title.workers.all()):
            worker.user = User.objects.create(username=worker.role, password='1234')
            worker.rate = index * 12
            if index % 2 == 0:
                worker.is_paid_by_pages = True
            worker.save()

        raw_provider = title.workers.get(role=Role.RAW_PROVIDER)
        cleaner = title.workers.get(role=Role.CLEANER)
        translator = title.workers.get(role=Role.TRANSLATOR)
        typesetter = title.workers.get(role=Role.TYPESETTER)
        quality_checker = title.workers.get(role=Role.QUALITY_CHECKER)

        raw_provider.days_for_work = 1
        cleaner.days_for_work = 2
        translator.days_for_work = 3
        typesetter.days_for_work = 7
        quality_checker.days_for_work = 5

        raw_provider.save()
        cleaner.save()
        translator.save()
        typesetter.save()
        quality_checker.save()

        self.chapter = Chapter.objects.create(title=title, chapter=1, tome=1, pages=20)

    def test_calculate_deadlines(self):
        # Order 0
        raw_provider = self.chapter.workers.get(role=Role.RAW_PROVIDER)
        self.assertEquals(raw_provider.deadline, self.chapter.start_date)
        raw_provider.upload_time = datetime.combine(raw_provider.deadline, datetime.min.time(),
                                                    tzinfo=timezone.get_current_timezone())
        raw_provider.is_done = True
        raw_provider.save()
        self.chapter.calculate_deadlines(Role.RAW_PROVIDER)

        # Order 1
        cleaner = self.chapter.workers.get(role=Role.CLEANER)
        translator = self.chapter.workers.get(role=Role.TRANSLATOR)

        self.assertEquals(translator.deadline, self.chapter.start_date + timezone.timedelta(days=3))
        self.assertEquals(cleaner.deadline, self.chapter.start_date + timezone.timedelta(days=2))
        cleaner.upload_time = datetime.combine(cleaner.deadline, datetime.min.time(),
                                               tzinfo=timezone.get_current_timezone())
        cleaner.is_done = True
        cleaner.save()
        translator.upload_time = datetime.combine(translator.deadline, datetime.min.time(),
                                                  tzinfo=timezone.get_current_timezone())
        translator.is_done = True
        translator.save()
        self.chapter.calculate_deadlines(Role.TRANSLATOR)

        # Order 2
        typesetter = self.chapter.workers.get(role=Role.TYPESETTER)
        self.assertEquals(typesetter.deadline, self.chapter.start_date + timezone.timedelta(days=10))
        typesetter.upload_time = datetime.combine(typesetter.deadline, datetime.min.time(),
                                                  tzinfo=timezone.get_current_timezone())
        typesetter.is_done = True
        typesetter.save()
        self.chapter.calculate_deadlines(Role.TYPESETTER)

        # Order 3
        quality_checker = self.chapter.workers.get(role=Role.QUALITY_CHECKER)
        self.assertEquals(quality_checker.deadline, self.chapter.start_date + timezone.timedelta(days=15))
        quality_checker.upload_time = datetime.combine(quality_checker.deadline, datetime.min.time(),
                                                       tzinfo=timezone.get_current_timezone())
        quality_checker.is_done = True
        quality_checker.save()
        self.chapter.calculate_deadlines(Role.QUALITY_CHECKER)

    def test_end(self):
        self.chapter.end()
        self.assertEquals(self.chapter.end_date, timezone.localdate())
        curator = self.chapter.workers.get(role=Role.CURATOR)
        self.assertTrue(curator.is_done)

    def test_set_published_status(self):
        url = 'https://docs.google.com/document/u/0/'
        for worker in self.chapter.workers.order_by('role').all():
            worker.upload(url=url)

        self.chapter.set_published_status()
        self.assertTrue(self.chapter.is_published)
        for worker in self.chapter.workers.order_by('role').all():
            if worker.is_paid_by_pages:
                balance = worker.rate * self.chapter.pages
            else:
                balance = worker.rate
            self.assertEquals(worker.user.balance, balance)
