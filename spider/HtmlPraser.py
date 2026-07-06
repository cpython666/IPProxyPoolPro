import json
import re

from lxml import etree


class HtmlPraser(object):
    PROXY_RE = re.compile(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}:\d{1,5}(?!\d)')

    @staticmethod
    def _unique(proxies):
        seen = set()
        proxylist = []
        for proxy in proxies:
            if not proxy or proxy in seen:
                continue
            seen.add(proxy)
            proxylist.append(proxy)

        return proxylist

    @staticmethod
    def _first_text(node, xpath):
        values = node.xpath(xpath)
        if not values:
            return ''

        value = values[0]
        if isinstance(value, str):
            return value.strip()

        return ''.join(value.itertext()).strip()

    @staticmethod
    def XpathPraser(response, parser):
        """Parse proxy rows with the historical parser config format."""
        proxylist = []
        root = etree.HTML(response)
        if root is None:
            return proxylist

        proxys = root.xpath(parser['pattern'])
        for proxy in proxys:
            ip = HtmlPraser._first_text(proxy, parser['position']['ip'])
            port = HtmlPraser._first_text(proxy, parser['position']['port'])
            if ip and port:
                proxylist.append(f'{ip}:{port}')

        return HtmlPraser._unique(proxylist)

    @staticmethod
    def RegexPraser(response, parser):
        """Parse plain text or HTML pages that expose ip:port directly."""
        pattern = parser.get('pattern')
        if pattern:
            proxies = re.findall(pattern, response)
        else:
            proxies = HtmlPraser.PROXY_RE.findall(response)

        return HtmlPraser._unique(proxies)

    @staticmethod
    def JsonPraser(response, parser):
        """Parse JSON APIs with a list of objects containing ip and port fields."""
        try:
            data = json.loads(response)
        except (TypeError, ValueError):
            return []

        items = data
        for key in parser.get('list_path', '').split('.'):
            if not key:
                continue
            if not isinstance(items, dict):
                return []
            items = items.get(key, [])

        if not isinstance(items, list):
            return []

        ip_field = parser.get('ip_field', 'ip')
        port_field = parser.get('port_field', 'port')
        proxies = []
        for item in items:
            if not isinstance(item, dict):
                continue
            ip = str(item.get(ip_field, '')).strip()
            port = str(item.get(port_field, '')).strip()
            if ip and port:
                proxies.append(f'{ip}:{port}')

        return HtmlPraser._unique(proxies)

    @staticmethod
    def parse(response, parser):
        parser_type = parser.get('type')
        if parser_type == 'xpath':
            return HtmlPraser.XpathPraser(response, parser)
        if parser_type in ('regex', 'regular'):
            return HtmlPraser.RegexPraser(response, parser)
        if parser_type == 'json':
            return HtmlPraser.JsonPraser(response, parser)

        return []
