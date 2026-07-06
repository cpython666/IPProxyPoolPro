from importlib import import_module

from IPProxyPoolPro import config


def get_http_client(client_name=None):
    selected_client = config.validate_request_client(client_name)
    if selected_client == 'requests':
        return import_module('requests')
    if selected_client == 'requests_go':
        return import_module('requests_go')
    if selected_client == 'curl_cffi':
        return import_module('curl_cffi.requests')

    raise ValueError(f'unsupported request client: {selected_client}')


def get(client_name, url, **kwargs):
    client = get_http_client(client_name)
    return client.get(url=url, **kwargs)
