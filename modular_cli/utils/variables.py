import getpass

# Logging
USER_NAME = getpass.getuser()
LOG_FORMAT_FOR_FILE = f'%(asctime)s [USER: {USER_NAME}][%(levelname)s] ' \
                      f'%(name)s,%(lineno)s %(message)s'

LOG_FORMAT_FOR_TERMNAL = f'%(asctime)s [%(levelname)s] USER: {USER_NAME} ' \
                         f'LOG: %(message)s'

# new tool folder name is '.m3modularcli'. It's resolved dynamically
# keeping backward compatibility
TOOL_FOLDER_NAME = 'm3modularcli'  # obsolete
TOOL_CONFIGURATION_FOLDER = '.modular_cli'  # new
TOOL_NAME = 'modular_cli'
LOG_FILE_NAME = 'modular_cli.log'
SUPPORTED_OS = ['nt', 'posix']
DEBUG_ENV_VARIABLE = 'MODULAR_CLI_DEBUG'
CUSTOM_LOG_PATH = 'LOG_PATH'

# Configuration
CREDENTIALS_FILE_NAME = 'credentials'
TEMPORARY_CREDS_FILENAME = 'temporary_creds.json'
COMMANDS_META = 'commands_meta.json'

DEFAULT_CONNECTION_TIMEOUT = 15

# 204
NO_CONTENT_RESPONSE_MESSAGE = 'Request is successful. No content returned'
# codes
RESPONSE_OK = 200
RESPONSE_CREATED = 201
RESPONSE_ACCEPTED = 202
RESPONSE_NO_CONTENT = 204
...
