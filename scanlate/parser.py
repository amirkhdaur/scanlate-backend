import requests
from urllib.parse import urlparse
from django.conf import settings

REMANGA_TOKEN = settings.REMANGA_TOKEN
REMANGA_TEAM_ID = settings.REMANGA_TEAM_ID


def create_title(remanga_url):
    parsed_url = urlparse(remanga_url)
    print(parsed_url.path)



if __name__ == '__main__':
    print(create_title('https://remanga.org/manga/the-strongest-soldier-of-the-modern-age-conquer-the-dungeon-of-another-world'))
