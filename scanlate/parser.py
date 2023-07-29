import requests
import json
from django.conf import settings
from .models import Title

REMANGA_TOKEN = settings.REMANGA_TOKEN
REMANGA_TEAM_ID = settings.REMANGA_TEAM_ID

session = requests.Session()
session.headers.update({'Authorization': f'Bearer {REMANGA_TOKEN}'})


def get_content(url):
    response = session.get(url)
    if response.status_code != 200:
        return None
    content = json.loads(response.text).get('content')
    return content


def create_title(title_slug, **kwargs):
    url = f'https://api.remanga.org/api/titles/{title_slug}/'
    content = get_content(url)
    if content is None:
        return content
    img = 'https://remanga.org' + content.get('img').get('high')
    name = content.get('rus_name')
    return Title.objects.create(name=name, slug=title_slug, img=img, **kwargs)


def check_chapters(title_slug):
    title_url = f'https://api.remanga.org/api/titles/{title_slug}/'
    title_content = get_content(title_url)
    branch_id = title_content.get('active_branch')

    chapters_url = f'https://api.remanga.org/api/titles/?branch_id={branch_id}?is_published=1'
    chapters_content = get_content(chapters_url)
    published_chapters = []
    for chapter in chapters_content:
        published_chapters.append([chapter.get('tome'), chapter.get('chapter')])

    title = Title.objects.get(slug=title_slug)
    for chapter in title.chapters.filter(is_published=False):
        if [chapter.tome, chapter.chapter] in published_chapters:
            chapter.set_published_status()
