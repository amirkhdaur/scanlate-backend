from django.test import TestCase
from django.utils import timezone
from datetime import datetime

from .models import *


class TeamTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Равочник', slug='raw-provider')
        Role.objects.create(name='Куратор', slug='curator')
        Role.objects.create(name='Клинер', slug='cleaner', order=0)
        Role.objects.create(name='Переводчик', slug='translator', order=0)
        Role.objects.create(name='Тайпер', slug='typesetter', order=1)
        Role.objects.create(name='Бета', slug='quality-checker', order=2)

        self.team = Team.objects.create(name='Team', slug='team')

    def test_create_title(self):
        title = self.team.create_title(name='Title', slug='title')

        self.assertIsNotNone(title)
        for role in Role.objects.all():
            self.assertTrue(title.workers.filter(role=role).exists())


class TitleTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Равочник', slug='raw-provider')
        Role.objects.create(name='Куратор', slug='curator')
        Role.objects.create(name='Клинер', slug='cleaner', order=0)
        Role.objects.create(name='Переводчик', slug='translator', order=0)
        Role.objects.create(name='Тайпер', slug='typesetter', order=1)
        Role.objects.create(name='Бета', slug='quality-checker', order=2)

        team = Team.objects.create(name='Team', slug='team')
        self.title = team.create_title(name='Title', slug='title')

    def test_create_chapter(self):
        url = 'https://docs.google.com/document/u/0/'
        chapter = self.title.create_chapter(tome=1, chapter=1, pages=10, url=url)

        self.assertIsNotNone(chapter)

        raw_provider = chapter.workers.get(role__slug='raw-provider')
        self.assertTrue(raw_provider.is_done)
        self.assertEquals(raw_provider.url, url)

        self.assertEquals(chapter.start_date, timezone.localdate() + timezone.timedelta(days=1))

    def test_create_chapter_with_start_date(self):
        url = 'https://docs.google.com/document/u/0/'
        start_date = timezone.localdate() + timezone.timedelta(days=6)
        chapter = self.title.create_chapter(tome=1, chapter=1, pages=10, url=url, start_date=start_date)

        self.assertIsNotNone(chapter)

        raw_provider = chapter.workers.get(role__slug='raw-provider')
        self.assertTrue(raw_provider.is_done)
        self.assertEquals(raw_provider.url, url)

        self.assertEquals(chapter.start_date, start_date)


class ChapterTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Равочник', slug='raw-provider')
        Role.objects.create(name='Куратор', slug='curator')
        Role.objects.create(name='Клинер', slug='cleaner', order=0)
        Role.objects.create(name='Переводчик', slug='translator', order=0)
        Role.objects.create(name='Тайпер', slug='typesetter', order=1)
        Role.objects.create(name='Бета', slug='quality-checker', order=2)

        team = Team.objects.create(name='Team', slug='team')
        title = team.create_title(name='Title', slug='title')
        self.chapter = title.create_chapter(chapter=1, tome=1, pages=20, url='https://docs.google.com/document/u/0/')

        cleaner = self.chapter.workers.get(role__slug='cleaner')
        translator = self.chapter.workers.get(role__slug='translator')
        typesetter = self.chapter.workers.get(role__slug='typesetter')

        cleaner.days_for_work = 2
        translator.days_for_work = 3
        typesetter.days_for_work = 7

        cleaner.save()
        translator.save()
        typesetter.save()

    def test_calculate_deadlines(self):
        self.chapter.calculate_deadlines(order=0)
        for worker in self.chapter.workers.filter(role__order=0).all():
            self.assertEquals(worker.deadline,
                              self.chapter.start_date + timezone.timedelta(days=(worker.days_for_work-1)))
            worker.upload_time = datetime.combine(worker.deadline, datetime.min.time(),
                                                  tzinfo=timezone.get_current_timezone())
            worker.save()

        self.chapter.calculate_deadlines(order=1)
        for worker in self.chapter.workers.filter(role__order=1).all():
            self.assertEquals(worker.deadline,
                              timezone.localdate() + timezone.timedelta(days=(7 + 3)))

    def test_end(self):
        self.chapter.end()

        self.assertEquals(self.chapter.end_date, timezone.localdate())

        curator = self.chapter.workers.get(role__slug='curator')
        self.assertTrue(curator.is_done)


class WorkerTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Равочник', slug='raw-provider')
        Role.objects.create(name='Куратор', slug='curator')
        Role.objects.create(name='Клинер', slug='cleaner', order=0)
        Role.objects.create(name='Переводчик', slug='translator', order=0)
        Role.objects.create(name='Тайпер', slug='typesetter', order=1)
        Role.objects.create(name='Бета', slug='quality-checker', order=2)

        team = Team.objects.create(name='Team', slug='team')
        title = team.create_title(name='Title', slug='title')
        self.chapter = title.create_chapter(chapter=1, tome=1, pages=20, url='https://docs.google.com/document/u/0/')

    def test_upload(self):
        url = 'https://docs.google.com/document/u/0/'
        for worker in self.chapter.workers.filter(role__order=0):
            worker.upload(url=url)
            self.assertEquals(worker.upload_time.replace(second=0, microsecond=0),
                              timezone.localtime().replace(second=0, microsecond=0))
            self.assertEquals(worker.url, url)
            self.assertTrue(worker.is_done)

        for worker in self.chapter.workers.filter(role__order=1):
            self.assertIsNotNone(worker.deadline)
            worker.upload(url=url)
            self.assertEquals(worker.upload_time.replace(second=0, microsecond=0),
                              timezone.localtime().replace(second=0, microsecond=0))
            self.assertEquals(worker.url, url)
            self.assertTrue(worker.is_done)

        quality_checker = self.chapter.workers.get(role__slug='quality-checker')
        self.assertIsNotNone(quality_checker.deadline)
        quality_checker.upload(url=url)
        self.assertEquals(quality_checker.upload_time.replace(second=0, microsecond=0),
                          timezone.localtime().replace(second=0, microsecond=0))
        self.assertEquals(quality_checker.url, url)
        self.assertTrue(quality_checker.is_done)
        self.assertIsNotNone(self.chapter.end_date)



