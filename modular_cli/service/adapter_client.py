import requests

from modular_cli.service.config import ConfigurationProvider
from modular_cli.utils.exceptions import (
    ModularCliConfigurationException, ModularCliTimeoutException,
)
from modular_cli.utils.logger import get_logger
from modular_cli.version import __version__

SYSTEM_LOG = get_logger(__name__)

CONF = ConfigurationProvider()

HTTP_GET = 'GET'
HTTP_POST = 'POST'
HTTP_PATCH = 'PATCH'
HTTP_DELETE = 'DELETE'


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

    def __make_request(self, resource: str, method: str, payload: dict = None,
                       params_to_log: dict = None) -> requests.Response:
        assert method in self.__method_to_function  # todo allow all methods
        method_func = self.__method_to_function[method]
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
            parameters.update(
                headers={'authorization': f'Bearer {self.__token}'}
            )
        else:
            parameters.update(auth=(self.__username, self.__secret))

        if parameters.get('headers'):
            parameters['headers'].update({'Cli-Version': __version__})
        else:
            parameters['headers'] = {'Cli-Version': __version__}

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
