import threading

import requests

from IPProxyPoolPro import config

try:
    import chardet
except ImportError:
    chardet = None


class Html_Downloader(object):
    _thread_local = threading.local()

    @staticmethod
    def _session():
        session = getattr(Html_Downloader._thread_local, 'session', None)
        if session is None:
            session = requests.Session()
            session.trust_env = False
            Html_Downloader._thread_local.session = session

        return session

    @staticmethod
    def download(url):
        try:
            response = Html_Downloader._session().get(
                url=url,
                headers=config.get_header(),
                timeout=config.FETCH_TIMEOUT,
            )
            response.raise_for_status()

            detected_encoding = None
            if chardet is not None:
                detected_encoding = chardet.detect(response.content).get('encoding')
            if detected_encoding:
                response.encoding = detected_encoding

            if len(response.content) < 200:
                raise ValueError('response content is too short')

            if 'kuaidaili.com' in url and '#list' not in response.text and '<table' not in response.text:
                raise ValueError('site returned an anti-bot or non-list page')

            return response.text
        except requests.RequestException as exc:
            print(f'页面下载失败: {url} ({exc})')
        except ValueError as exc:
            print(f'页面内容异常: {url} ({exc})')

        return False
