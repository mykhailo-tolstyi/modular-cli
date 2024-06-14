import json
import os
from functools import wraps

import click
import yaml
from prettytable import PrettyTable

from modular_cli import ENTRY_POINT
from modular_cli.service.config import (
    add_data_to_config, ROOT_ADMIN_VERSION,
)
from modular_cli.service.help_client import (
    SetupCommandHandler, LoginCommandHandler, CleanupCommandHandler,
    EnableAutocompleteCommandHandler, DisableAutocompleteCommandHandler,
    VersionCommandHandler,
)
from modular_cli.service.initializer import init_configuration
from modular_cli.utils.exceptions import (
    ModularCliBadRequestException, ModularCliBaseException,
    HTTP_CODE_EXCEPTION_MAPPING,
)
from modular_cli.utils.logger import get_logger

_LOG = get_logger(__name__)


def init_config(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        init_configuration()
        return func(*args, **kwargs)

    return wrapper


JSON_VIEW = 'json'
TABLE_VIEW = 'table'
HELP_COMMAND = 'help'
COMMAND_KEY = 'command'
CONFIGURATION_COMMAND = 'configuration_command'

CLI_VIEW = 'cli'
ERROR_STATUS = 'FAILED'
FILE_NAME = 'modular-cli.log'
SUCCESS_STATUS = 'SUCCESS'
MODULAR_CLI_STATUS = 'Status'
MODULAR_CLI_CODE = 'Code'
MODULAR_CLI_ERROR_TYPE = 'ErrorType'
MODULAR_CLI_MESSAGE = 'Message'
MODULAR_CLI_META = 'Meta'
MODULAR_CLI_TABLE_TITLE = 'table_title'
MODULAR_CLI_ITEMS = 'items'
MODULAR_CLI_WARNINGS = 'Warnings'
MODULAR_CLI_RESPONSE = 'Response'
MAX_COLUMNS_WIDTH = 30
POSITIVE_ANSWERS = ['y', 'yes']
CONFIRMATION_MESSAGE = 'The command`s response is pretty huge and the ' \
                       'result table structure can be broken.\nDo you want ' \
                       'to show the response in the JSON format? [y/n]: '

SETUP_COMMAND_HELP = \
    f'Usage: {ENTRY_POINT} setup [parameters]{os.linesep}' \
    f'Parameters:{os.linesep}     --username,   Access key ' \
    f'associated with the Maestro user{os.linesep}     --password,   Secret ' \
    f'key associated with the Maestro user{os.linesep}     --api_path,   ' \
    f'Address of the Maestro environment.'
LOGIN_COMMAND_HELP = f'{os.linesep}Usage: {ENTRY_POINT} login{os.linesep}' \
                     f'{os.linesep}Returns JWT token and commands meta in ' \
                     f'accordance with the user\'s permissions'
CLEANUP_COMMAND_HELP = f'{os.linesep}Usage: {ENTRY_POINT} cleanup [parameters]' \
                       f'{os.linesep}{os.linesep}Removes all the ' \
                       f'configuration data related to the tool.'
INVOCATIONS_COUNTER = 0


class TextColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @classmethod
    def _wrap(cls, color: str, string: str) -> str:
        return color + string + cls.ENDC

    @classmethod
    def yellow(cls, string: str) -> str:
        return cls._wrap(cls.WARNING, string)


def check_and_extract_received_params(arguments, required_params):
    result = []
    missing = []
    for arg, required in required_params.items():
        if arg in arguments:
            result.append(arguments[arguments.index(arg) + 1])
        else:
            if required:
                missing.append(arg.replace('--', ''))
    if missing:
        raise ModularCliBadRequestException(
            f'The following parameters are missing: {", ".join(missing)}')
    return result


def dynamic_dispatcher(func):
    @wraps(func)
    def wrapper(ctx, *args, **kwargs):
        try:
            if not ctx.args:
                params = {HELP_COMMAND: True}
                return func(**params)

            view_type = CLI_VIEW
            if ctx.params.get(TABLE_VIEW):
                view_type = TABLE_VIEW
            if ctx.params.get(JSON_VIEW):
                view_type = JSON_VIEW
            if ctx.args[0] in ['setup', 'login', 'cleanup', 'version',
                               'enable_autocomplete', 'disable_autocomplete']:
                response = configuration_executor(config_command=ctx.args[0],
                                                  config_command_help=
                                                  ctx.params['help'],
                                                  config_params=ctx.args)
                return response

            params_indexes = [
                ctx.args.index(arg) for arg in ctx.args if arg.startswith('-')
            ]
            if params_indexes:
                command_end_index, *_ = params_indexes
                requested_command = ctx.args[:command_end_index]
                parameters = ctx.args[command_end_index:]
                response = func(help=kwargs.get('help'),
                                command=requested_command,
                                parameters=parameters,
                                view_type=view_type)

            else:
                requested_command = ctx.args
                parameters = {}
                response = func(help=kwargs.get('help'),
                                command=requested_command,
                                parameters=parameters,
                                view_type=view_type)
            return response

        except ModularCliBaseException as e:
            response = CommandResponse(message=str(e), code=e.code)
            return response

    return wrapper


def process_meta(server_meta):
    new_meta = {}
    for mount_point, meta in server_meta.items():
        bare_module_name = mount_point.replace('/', '')
        if not bare_module_name:  # in case of / mount point
            add_data_to_config(name=ROOT_ADMIN_VERSION, value=meta['version'])
            new_meta.update(meta.get('body'))
        else:
            new_meta.update({bare_module_name: meta})
    return new_meta


CONFIG_COMMAND_HANDLER_MAPPING = {
    'setup': SetupCommandHandler,
    'login': LoginCommandHandler,
    'cleanup': CleanupCommandHandler,
    'enable_autocomplete': EnableAutocompleteCommandHandler,
    'disable_autocomplete': DisableAutocompleteCommandHandler,
    'version': VersionCommandHandler
}


def configuration_executor(config_command, config_command_help, config_params):
    config_command_class = CONFIG_COMMAND_HANDLER_MAPPING[config_command]
    initiate_appropriate_command = config_command_class(
        config_command_help=config_command_help,
        config_params=config_params)
    return initiate_appropriate_command.process_passed_command()


def cli_response():
    def internal(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            view_format = JSON_VIEW
            response = func(*args, **kwargs)

            pretty_response = ResponseFormatter(
                function_result=response, view_format=view_format,
            ).prettify_response()
            click.echo(pretty_response)

        return wrapper

    return internal


class ResponseDecorator:
    """
    Wrapper for formatting cli command response
    :param stdout: function which prints response to the end user
    :param error_message: message that will be displayed in case command
        failed to execute
    :param secured_params: value of this parameters will be replaced
        with asterisks.
    :return:
    """
    view_format = 'TEST'

    def __init__(self, stdout, error_message, secured_params=None):
        self.stdout = stdout
        self.error_message = error_message
        self.secured_params = secured_params

    def __call__(self, fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            _FUNC_LOG = _LOG.getChild(fn.__name__)  # todo remove ?
            view_format = CLI_VIEW
            table_format = kwargs.pop(TABLE_VIEW, False)
            json_format = kwargs.pop(JSON_VIEW, False)
            if table_format:
                view_format = TABLE_VIEW
            elif json_format:
                view_format = JSON_VIEW
            global VIEW_FORMAT
            global INVOCATIONS_COUNTER
            VIEW_FORMAT = view_format
            INVOCATIONS_COUNTER += 1
            resp = fn(*args, **kwargs)  # CommandResponse
            INVOCATIONS_COUNTER -= 1
            if not isinstance(resp, CommandResponse):
                warn_message = ['Response is broken and does not match '
                                'CommandResponse object']
                _FUNC_LOG.warning(warn_message)
                resp = CommandResponse(message=resp, warnings=warn_message)
            if not INVOCATIONS_COUNTER:
                func_result = ResponseFormatter(function_result=resp,
                                                view_format=view_format)
                response = self.stdout(func_result.prettify_response())
                return response

        return decorated


class CommandResponse:
    def __init__(
            self,
            code=200,
            message: str | None = None,
            items: list | None = None,
            warnings=None,
            table_title=None,
            **kwargs
    ):
        """
        Considering kwargs to be extra attributes that are specific to each
        module
        """
        self.code = code
        self.message = message
        self.warnings = warnings or []
        self.items = items
        self.table_title = table_title
        self.meta = dict(kwargs)
        if not (self.table_title and self.items) and self.message is None:
            self.warnings.append(
                'Please provide "table_title" and "items" or "message" '
                'parameter')


class ResponseFormatter:
    def __init__(self, function_result, view_format):
        self.view_format = view_format
        self.function_result = function_result
        self.format_to_process_method = {
            CLI_VIEW: self.process_cli_view,
            JSON_VIEW: self.process_json_view,
            TABLE_VIEW: self.process_table_view
        }

    @staticmethod
    def _prettify_warnings(warnings: list):
        return f'{os.linesep}WARNINGS:{os.linesep}' + \
               f'{os.linesep}'.join(str(i + 1) + '. ' + warnings[i]
                                    for i in range(len(warnings)))

    @staticmethod
    def is_response_success(response_meta: CommandResponse):
        return 200 <= response_meta.code <= 206  # + 207, 208, 226

    @staticmethod
    def unpack_success_result_values(response_meta: CommandResponse):
        success_code = response_meta.code
        warnings = response_meta.warnings
        message = response_meta.message
        items = response_meta.items
        table_title = response_meta.table_title
        return success_code, warnings, message, items, table_title

    @staticmethod
    def unpack_error_result_values(response_meta: CommandResponse):
        error_code = response_meta.code
        error_type = HTTP_CODE_EXCEPTION_MAPPING[error_code].__name__
        message = response_meta.message
        return error_type, error_code, message

    def process_cli_view(self, status: str, response_meta: CommandResponse):
        if status == ERROR_STATUS:
            error_type, error_code, message = self.unpack_error_result_values(
                response_meta=response_meta)
            return f'Error:{os.linesep}{message}'
        elif status == SUCCESS_STATUS:
            success_code, warnings, message, items, table_title = \
                self.unpack_success_result_values(response_meta=response_meta)
            if table_title and items:
                return self.process_table_view(status=status,
                                               response_meta=response_meta)
            result_message = f'Response:{os.linesep}{message}'
            if warnings:
                result_message += self._prettify_warnings(warnings)
            return result_message

    def process_json_view(self, status: str, response_meta: CommandResponse):
        if status == ERROR_STATUS:
            error_type, error_code, message = self.unpack_error_result_values(
                response_meta=response_meta)
            return json.dumps({
                MODULAR_CLI_STATUS: status,
                MODULAR_CLI_CODE: error_code,
                MODULAR_CLI_ERROR_TYPE: error_type,
                MODULAR_CLI_MESSAGE: message,
                MODULAR_CLI_META: response_meta.meta
            }, indent=4)
        elif status == SUCCESS_STATUS:
            success_code, warnings, message, items, table_title = \
                self.unpack_success_result_values(response_meta=response_meta)
            if table_title and items:
                return json.dumps({
                    MODULAR_CLI_STATUS: status,
                    MODULAR_CLI_CODE: success_code,
                    MODULAR_CLI_TABLE_TITLE: table_title,
                    MODULAR_CLI_ITEMS: items,
                    MODULAR_CLI_WARNINGS: warnings,
                    MODULAR_CLI_META: response_meta.meta
                }, indent=4)
            return json.dumps({
                MODULAR_CLI_STATUS: status,
                MODULAR_CLI_CODE: success_code,
                MODULAR_CLI_MESSAGE: message,
                MODULAR_CLI_WARNINGS: warnings,
                MODULAR_CLI_META: response_meta.meta
            }, indent=4)

    def process_table_view(self, status: str, response_meta: CommandResponse):
        response = PrettyTable()
        if status == ERROR_STATUS:
            response.field_names = [MODULAR_CLI_STATUS,
                                    MODULAR_CLI_CODE,
                                    MODULAR_CLI_MESSAGE]
            response._max_width = {MODULAR_CLI_STATUS: 10,
                                   MODULAR_CLI_CODE: 5,
                                   MODULAR_CLI_MESSAGE: 70}
            error_type, error_code, message = self.unpack_error_result_values(
                response_meta=response_meta)
            response.add_row([status, error_code, message])
            response = response.__str__()
            return response
        elif status == SUCCESS_STATUS:
            success_code, warnings, message, items, table_title = \
                self.unpack_success_result_values(
                    response_meta=response_meta)
            if message:
                response.field_names = [MODULAR_CLI_STATUS,
                                        MODULAR_CLI_CODE,
                                        MODULAR_CLI_RESPONSE]
                response._max_width = {MODULAR_CLI_STATUS: 10,
                                       MODULAR_CLI_CODE: 5,
                                       MODULAR_CLI_RESPONSE: 70}
                response.add_row([status, success_code, message])
            elif table_title and items:
                all_values = {}
                uniq_table_headers = []
                width_table_columns = {}
                for each_item in items:
                    if not isinstance(each_item, dict):
                        each_item = {'Result': each_item}
                    for table_key, table_value in each_item.items():
                        if all_values.get(table_key):
                            all_values[table_key].append(table_value)
                        else:
                            all_values[table_key] = [table_value]
                        uniq_table_headers.extend(
                            [table_key for table_key in
                             each_item.keys()
                             if table_key not in uniq_table_headers])
                        if not width_table_columns.get(table_key) \
                                or width_table_columns.get(table_key) \
                                < len(str(table_value)):
                            width_table_columns[table_key] \
                                = len(str(table_value))
                import itertools
                response.field_names = uniq_table_headers
                response._max_width = {each: MAX_COLUMNS_WIDTH for each in
                                       uniq_table_headers}
                try:
                    if MAX_COLUMNS_WIDTH * len(uniq_table_headers) > \
                            os.get_terminal_size().columns and \
                            input(CONFIRMATION_MESSAGE).lower().strip() \
                            in POSITIVE_ANSWERS:
                        return self.process_json_view(status, response_meta)
                except Exception:
                    pass
                last_string_index = 0
                # Fills with an empty content absent items attributes to
                # align the table
                table_rows = itertools.zip_longest(
                    *[j for i, j in all_values.items()], fillvalue='')
                for lst in table_rows:
                    response.add_row(lst)
                    row_separator = ['-' * min(
                        max(width_table_columns[uniq_table_headers[i]],
                            len(str(uniq_table_headers[i]))),
                        30) for i in range(len(uniq_table_headers))]
                    response.add_row(row_separator)
                    last_string_index += 2
                response.del_row(last_string_index - 1)

            # ----- showing meta in table view -----
            meta = response_meta.meta
            if meta:
                meta = TextColors.yellow(
                    yaml.dump({
                        self.format_title(k): v for k, v in meta.items()
                    })
                )
                response = meta + os.linesep + str(response)
            # ----- showing meta in table view -----

            response = (table_title + os.linesep if table_title else str()) + \
                       str(response)
            if response_meta.warnings:
                response += self._prettify_warnings(response_meta.warnings)

        return response

    def prettify_response(self):
        status = SUCCESS_STATUS if self.is_response_success(
            response_meta=self.function_result) else ERROR_STATUS
        view_processor = self.format_to_process_method[self.view_format]
        prettified_response = view_processor(
            status=status, response_meta=self.function_result)
        return prettified_response

    @staticmethod
    def format_title(title: str) -> str:
        """
        Human-readable
        """
        return title.replace('_', ' ').capitalize()
