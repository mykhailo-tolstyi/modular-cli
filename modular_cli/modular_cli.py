from json import JSONDecodeError
from http import HTTPStatus
import click

from modular_cli.service.decorators import (
    dynamic_dispatcher, CommandResponse, ResponseDecorator,
)
from modular_cli.service.help_client import (
    retrieve_commands_meta_content, HelpProcessor, LoginCommandHandler,
)
from modular_cli.service.initializer import init_configuration
from modular_cli.service.request_processor import prepare_request
from modular_cli.service.utils import find_token_meta
from modular_cli.utils.exceptions import ModularCliInternalException
from modular_cli.utils.variables import NO_CONTENT_RESPONSE_MESSAGE

CONTEXT_SETTINGS = dict(allow_extra_args=True,
                        ignore_unknown_options=True)
# if you are going to change the value of the next line - please change
# correspond value in Modular-API
RELOGIN_TEXT = 'The provided token has expired due to updates in ' \
               'commands meta. Please get a new token from \'/login\' ' \
               'resource'


@click.command(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.option('--help', is_flag=True, default=False)
@click.option('--json', is_flag=True, default=False)
@click.option('--table', is_flag=True, default=False)
@ResponseDecorator(click.echo, 'Response is broken.')
@dynamic_dispatcher
def modular_cli(help, command=None, parameters=None, view_type=None):
    commands_meta = retrieve_commands_meta_content()
    token_meta = find_token_meta(commands_meta=commands_meta,
                                 specified_tokens=command)
    is_help = __is_help_required(token_meta=token_meta,
                                 specified_parameters=parameters,
                                 help_flag=help)
    if is_help:
        help_processor = HelpProcessor(requested_command=command,
                                       commands_meta=commands_meta)
        help_message = help_processor.get_help_message(token_meta=token_meta)
        click.echo(help_message)
        exit()
    resource, method, parameters, params_to_log = prepare_request(
        token_meta=token_meta,
        passed_parameters=parameters)
    adapter_sdk = init_configuration()

    response = adapter_sdk.execute_command(
        resource=resource, parameters=parameters,
        method=method, params_to_log=params_to_log)
    # automated re-login ========================================================
    # in case if Modular-API return status code "426" we make login command from
    # Modular-CLI to get updated meta and then execute original command again
    if (response.status_code == 426) \
       or \
       (response.status_code == 401 and RELOGIN_TEXT in response.text):
        LoginCommandHandler(config_command_help=False,
                            config_params=['login']).execute_command()
        fresh_adapter_sdk = init_configuration()
        response = fresh_adapter_sdk.execute_command(
            resource=resource, parameters=parameters,
            method=method, params_to_log=params_to_log)
    # ===========================================================================
    if response.status_code == HTTPStatus.NO_CONTENT.value:
        return CommandResponse(message=NO_CONTENT_RESPONSE_MESSAGE)
    try:
        response_body = response.json()
    except JSONDecodeError:
        return CommandResponse(
            message='Can not parse response into json. Please check logs',
            code=400,
        )
    except Exception:
        raise ModularCliInternalException(
            'Unexpected error happened. Please contact the Maestro support team.'
        )

    return CommandResponse(**response_body, code=response.status_code)


def __is_help_required(token_meta, specified_parameters, help_flag):
    if help_flag:
        return help_flag
    if not token_meta.get('route'):
        return True
    required_parameters = [
        param for param in token_meta.get('parameters') if param.get('required')
    ]
    return required_parameters and not specified_parameters
