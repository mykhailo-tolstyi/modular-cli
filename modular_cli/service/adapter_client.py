import os

import requests

from modular_cli.service.config import ConfigurationProvider
from modular_cli.utils.logger import get_logger, get_user_logger
from modular_cli.utils.exceptions import ModularCliConfigurationException, \
    ModularCliTimeoutException

SYSTEM_LOG = get_logger('service.adapter_client')
USER_LOG = get_user_logger('user')

CONF = ConfigurationProvider()

HTTP_GET = 'GET'
HTTP_POST = 'POST'
HTTP_PATCH = 'PATCH'
HTTP_DELETE = 'DELETE'

ALLOWED_METHODS = [HTTP_GET, HTTP_POST, HTTP_PATCH, HTTP_DELETE]


class AdapterClient:

    def __init__(self, adapter_api, username, secret, token):
        self.__api_link = adapter_api
        self.__username = username
        self.__secret = secret
        self.__token = token
        self.__method_to_function = {
            HTTP_GET: requests.get,
            HTTP_POST: requests.post,
            HTTP_PATCH: requests.patch,
            HTTP_DELETE: requests.delete
        }
        SYSTEM_LOG.info('Adapter SDK has been initialized')

    @staticmethod
    def get_tool_version():
        from pathlib import Path

        version = {}
        ver_path = os.path.join(Path(__file__).parent.parent.parent, "version.py")

        with open(ver_path) as fp:
            exec(fp.read(), version)

        return version['__version__']

    def __make_request(self, resource: str, method: str, payload: dict = None,
                       params_to_log: dict = None) -> requests.Response:
        if method not in ALLOWED_METHODS:
            SYSTEM_LOG.error(f'Requested method {method} in not allowed. '
                             f'Allowed methods: {ALLOWED_METHODS}')
            USER_LOG.error('Sorry, error happened. '
                           'Please contact the tool support team.')
        method_func = self.__method_to_function.get(method)
        parameters = dict(url=f'{self.__api_link}{resource}')
        if method == HTTP_GET:
            parameters.update(params=payload)
        else:
            parameters.update(json=payload)
        SYSTEM_LOG.debug(
            f'API request info: Resource: {resource}; '
            f'Parameters: {params_to_log if params_to_log else {}}; '
            f'Method: {method}.')
        if self.__token and resource != '/login':
            parameters.update(headers=
                              {'authorization': f'Bearer {self.__token}'})
        else:
            parameters.update(auth=(self.__username, self.__secret))

        if parameters.get('headers'):
            parameters['headers'].update({'Cli-Version': self.get_tool_version()})
        else:
            parameters['headers'] = {'Cli-Version': self.get_tool_version()}

        try:
            response = method_func(**parameters)
        except requests.exceptions.ConnectTimeout:
            message = 'Failed to establish connection with the server due ' \
                      'to exceeded timeout. Probably a security group ' \
                      'denied the request'
            SYSTEM_LOG.exception(message)
            raise ModularCliTimeoutException(message)
        except requests.exceptions.ConnectionError:
            raise ModularCliConfigurationException(
                'Provided configuration api_link is invalid or outdated. '
                'Please contact the tool support team.')
        SYSTEM_LOG.debug(f'API response info: {response}')
        return response

    def login(self) -> requests.Response:
        request = {"meta": "true"}
        return self.__make_request(resource='/login', method=HTTP_GET,
                                   payload=request)

    def execute_command(self, resource, parameters, method,
                        params_to_log) -> requests.Response:
        return self.__make_request(resource=resource,
                                   payload=parameters,
                                   method=method,
                                   params_to_log=params_to_log)
