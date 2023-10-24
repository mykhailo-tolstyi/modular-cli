from abc import ABC


class ModularCliBaseException(ABC, Exception):
    """
    Base Modular-CLI exception
    """


class ModularCliBadRequestException(ModularCliBaseException):
    """
    Incoming request to Modular-CLI is invalid due to parameters invalidity.
    """
    code = 400


class ModularCliConfigurationException(ModularCliBaseException):
    """
    Internal service is not configured: General configuration mismatch
    """
    code = 503


class ModularCliServiceTemporaryUnavailableException(ModularCliBaseException):
    """
    Internal service is not configured: General configuration mismatch
    """
    code = 503


class ModularCliUnauthorizedException(ModularCliBaseException):
    """
    CLI: provided credentials to AWS/Minio/Vault/MongoDB are invalid
    API: provided API credentials are invalid.
    """
    code = 401


class ModularCliForbiddenException(ModularCliBaseException):
    """
    The credentials are valid, but permission policy denies a command execution
    for requestor
    """
    code = 403


class ModularCliNotFoundException(ModularCliBaseException):
    """
    The requested resource has not been found
    """
    code = 404


class ModularCliTimeoutException(ModularCliBaseException):
    """
    Failed to respond in expected time range
    """
    code = 408


class ModularCliConflictException(ModularCliBaseException):
    """
    Incoming request processing failed due to environment state is incompatible
    with requested command
    """
    code = 409


class ModularCliInternalException(ModularCliBaseException):
    """
    Modular-CLI failed to process incoming requests due to an error in the code.
    It’s a developer’s mistake.
    """
    code = 500


class ModularCliBadGatewayException(ModularCliBaseException):
    """
    Modular-CLI obtained the Error message from 3rd party application it is
    integrated with to satisfy the user's command.
    """
    code = 502


class ModularCliGatewayTimeoutException(ModularCliBaseException):
    """
    Should be raised in case Modular-CLI did not get response from third party
    service (server, AWS service, Minio, Vault, MongoDB) requested in scope
    of the command execution.
    """
    code = 504


class ModularCliUpdateRequiredException(ModularCliBaseException):
    """
    Should be raised if client use obsolete Modular-API commands meta
    """
    code = 426


HTTP_CODE_EXCEPTION_MAPPING = {
    400: ModularCliBadRequestException,
    401: ModularCliUnauthorizedException,
    403: ModularCliForbiddenException,
    404: ModularCliNotFoundException,
    408: ModularCliTimeoutException,
    409: ModularCliConflictException,
    426: ModularCliUpdateRequiredException,
    500: ModularCliInternalException,
    502: ModularCliBadGatewayException,
    503: ModularCliServiceTemporaryUnavailableException,
    504: ModularCliGatewayTimeoutException
}
