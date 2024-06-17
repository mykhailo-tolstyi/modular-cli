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

import logging
import logging.config
import os
from pathlib import Path

from modular_cli.utils.variables import (
    LOG_FILE_NAME,
    TOOL_CONFIGURATION_FOLDER,
    ENV_LOG_PATH,
    ENV_LOG_LEVEL,
    ENV_CLI_DEBUG
)


def _get_logs_path() -> Path:
    """
    Returns logs that exists
    :return:
    """
    default = str(Path.home() / TOOL_CONFIGURATION_FOLDER / 'logs')
    path = os.getenv(ENV_LOG_PATH, default)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        logging.getLogger().warning(
            f'Cannot access {path}. Writing logs to {default}'
        )
        path = default
        os.makedirs(path, exist_ok=True)
    return Path(path).resolve()


LOGS_PATH = _get_logs_path()
LOGS_FILE = LOGS_PATH / LOG_FILE_NAME

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'main_formatter': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
        },
    },
    'handlers': {
        'console_handler': {
            'class': 'logging.StreamHandler',
            'formatter': 'main_formatter'
        },
        'file_handler': {
            'class': 'logging.FileHandler',
            'filename': LOGS_FILE,
            'formatter': 'main_formatter',
        }
    },
    'loggers': {
        'modular_cli': {
            'level': os.getenv(ENV_LOG_LEVEL, 'INFO'),
            'handlers': ['file_handler', 'console_handler'] if os.getenv(
                ENV_CLI_DEBUG) else ['file_handler']
        },
    }
})


def get_logger(name: str, level=None) -> logging.Logger:
    log = logging.getLogger(name)
    if level:
        log.setLevel(level)
    return log
