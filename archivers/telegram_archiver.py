import os
import requests
from bs4 import BeautifulSoup

from .base_archiver import Archiver, ArchiveResult


class TelegramArchiver(Archiver):
    name = "telegram"

    def download(self, url, check_if_exists=False):
        # detect URLs that we definitely cannot handle
        if 't.me' != self.get_netloc(url):
            return False

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
        }
        status = "success"

        original_url = url

        # TODO: check if we can do this more resilient to variable URLs
        if url[-8:] != "?embed=1":
            url += "?embed=1"

        t = requests.get(url, headers=headers)
        s = BeautifulSoup(t.content, 'html.parser')
        video = s.find("video")

        if video is None:
            return False  # could not find video

        video_url = video.get('src')
        video_id = video_url.split('/')[-1].split('?')[0]
        key = self.get_key(video_id)

        filename = 'tmp/' + key
        cdn_url = self.storage.get_cdn_url(key)

        if check_if_exists and self.storage.exists(key):
            status = 'already archived'

        v = requests.get(video_url, headers=headers)

        with open(filename, 'wb') as f:
            f.write(v.content)

        if status != 'already archived':
            self.storage.upload(filename, key)

        # extract duration from HTML
        duration = s.find_all('time')[0].contents[0]
        if ':' in duration:
            duration = float(duration.split(':')[0]) * 60
            + float(duration.split(':')[1])
        else:
            duration = float(duration)

        # process thumbnails
        key_thumb, thumb_index = self.get_thumbnails(filename, key, duration=duration)
        os.remove(filename)

        return ArchiveResult(status=status, cdn_url=cdn_url, thumbnail=key_thumb, thumbnail_index=thumb_index,
                             duration=duration, title=original_url, timestamp=s.find_all('time')[1].get('datetime'))
