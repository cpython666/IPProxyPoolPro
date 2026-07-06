import chardet
import requests

from IPProxyPoolPro import config


class Html_Downloader(object):
    @staticmethod
    def download(url):
        try:
            response = requests.get(url=url, headers=config.get_header(), timeout=config.TIMEOUT)
            response.raise_for_status()

            detected_encoding = chardet.detect(response.content).get('encoding')
            if detected_encoding:
                response.encoding = detected_encoding

            if len(response.content) < 200:
                raise ValueError('response content is too short')

            return response.text
        except requests.RequestException as exc:
            print(f'页面下载失败: {url} ({exc})')
        except ValueError as exc:
            print(f'页面内容异常: {url} ({exc})')

        return False
