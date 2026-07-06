from lxml import etree


class HtmlPraser(object):
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

        return proxylist
