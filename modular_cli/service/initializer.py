import os

from modular_cli.service.config import ConfigurationProvider, get_credentials_folder
from modular_cli.utils.logger import get_logger
from modular_cli.utils.variables import CREDENTIALS_FILE_NAME

SYSTEM_LOG = get_logger('modular_cli.service.initializer')


def init_configuration():
    from modular_cli.service.adapter_client import AdapterClient
    config_path = get_credentials_folder() / CREDENTIALS_FILE_NAME
    if os.path.exists(config_path):
        config = ConfigurationProvider()
        return AdapterClient(adapter_api=config.api_link,
                             username=config.username,
                             secret=config.password,
                             token=config.access_token)
    else:
        SYSTEM_LOG.info(f'Configuration is missing by path {config_path}. '
                        f'Initialization skipped.')
