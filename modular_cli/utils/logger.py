# Copyright 2018 EPAM Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# [http://www.apache.org/licenses/LICENSE-2.0]
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from modular_cli.utils.variables import (
    SUPPORTED_OS, LOG_FORMAT_FOR_FILE, LOG_FILE_NAME, USER_NAME,
    TOOL_FOLDER_NAME, TOOL_CONFIGURATION_FOLDER,
    TOOL_NAME, LOG_FORMAT_FOR_TERMNAL, DEBUG_ENV_VARIABLE,
    CUSTOM_LOG_PATH)
from pathlib import Path
from logging import (DEBUG, getLogger, Formatter, StreamHandler, INFO,
                     FileHandler, WARNING)


def is_env_variable(variable_name):
    variable_value = os.getenv(variable_name)
    if variable_value and variable_value.lower() == 'true':
        return True
    return False


def get_log_path():
    log_path = os.getenv(CUSTOM_LOG_PATH)
    return log_path


modular_cli_logger = getLogger(TOOL_NAME)
modular_cli_logger.propagate = False


def create_path_for_logs():
    """
    Initializing the path for the log file.

      This function determines the type of system and, based on it,
      returns the path to create the log file.
    """

    os_name = os.name
    path_home = Path.home()
    _LOG = get_custom_terminal_logger(__name__, WARNING)
    _LOG.propagate = False

    # Determining the type of operating system
    if os_name not in SUPPORTED_OS or not path_home:
        _LOG.warning(
            f"Current OS:[{os_name}] is not supported or environment variable"
            f" ${path_home} is not set. The log file will be stored by path "
            f"{os.getcwd()}"
        )
        return LOG_FILE_NAME

    # Creating full name of the path to the log directory
    custom_log_path = get_log_path()
    if custom_log_path:
        path = os.path.join(custom_log_path, TOOL_FOLDER_NAME, USER_NAME)
    elif os_name == 'posix':
        path = os.path.join('/var/log', TOOL_FOLDER_NAME, USER_NAME)
    else:
        # hard to import due to the way code is structured
        # path = get_credentials_folder() / 'log'
        path = Path.home() / TOOL_CONFIGURATION_FOLDER / 'log'
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError:
            _LOG.warning(
                f"No access: {path}. To find the log file, check the directory"
                f" from which you called the command"
            )
            return LOG_FILE_NAME
    full_path = os.path.join(path, LOG_FILE_NAME)
    return full_path


def get_file_handler(level=INFO):
    file_handler = FileHandler(filename=create_path_for_logs())
    file_handler.setLevel(level)
    file_handler.setFormatter(
        Formatter(LOG_FORMAT_FOR_FILE, '%Y-%m-%d %H:%M:%S'))
    return file_handler


def get_custom_terminal_logger(name, log_level_for_terminal=INFO,
                               log_level_logger=None):
    module_logger = getLogger(name)
    if not log_level_logger:
        log_level_logger = log_level_for_terminal
    module_logger.setLevel(log_level_logger)
    module_logger.addHandler(get_stream_handler(log_level_for_terminal))
    return module_logger


def get_stream_handler(level=WARNING):
    stream_handler = StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(Formatter(LOG_FORMAT_FOR_TERMNAL))
    return stream_handler


def get_logger(log_name, level=DEBUG):
    module_logger = modular_cli_logger.getChild(log_name)
    if level:
        module_logger.setLevel(level)
    if is_env_variable(DEBUG_ENV_VARIABLE):
        module_logger.addHandler(get_custom_terminal_logger(
            name=log_name,
            log_level_for_terminal=WARNING))

    module_logger.addHandler(get_file_handler(level))
    return module_logger


def get_user_logger(log_name, level=INFO):
    cli_user_logger = getLogger('modular_cli.user')
    cli_user_logger.addHandler(get_custom_terminal_logger(log_name))
    module_logger = cli_user_logger.getChild(log_name)
    if level:
        module_logger.setLevel(level)
    return module_logger
