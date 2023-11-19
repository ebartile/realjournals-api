"""
Handled exceptions raised by REST framework.

In addition Django's built in 403 and 404 exceptions are handled.
(`django.http.Http404` and `django.core.exceptions.PermissionDenied`)
"""

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from django.http import Http404
from rest_framework.views import set_rollback
from rest_framework import response
from rest_framework import exceptions, status
import math


class APIException(Exception):
    """
    Base class for REST framework exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = ""

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class ParseError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Malformed request.")


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Incorrect authentication credentials.")


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = _("Authentication credentials were not provided.")


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = _("You do not have permission to perform this action.")


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _("Method '%s' not allowed.")

    def __init__(self, method, detail=None):
        self.detail = (detail or self.default_detail) % method


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = _("Could not satisfy the request's Accept header")

    def __init__(self, detail=None, available_renderers=None):
        self.detail = detail or self.default_detail
        self.available_renderers = available_renderers


class UnsupportedMediaType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = _("Unsupported media type '%s' in request.")

    def __init__(self, media_type, detail=None):
        self.detail = (detail or self.default_detail) % media_type


class Throttled(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = _("Request was throttled.")
    extra_detail = _("Expected available in %d second%s.")

    def __init__(self, wait=None, detail=None):
        if wait is None:
            self.detail = detail or self.default_detail
            self.wait = None
        else:
            format = "%s%s" % ((detail or self.default_detail), self.extra_detail)
            self.detail = format % (wait, wait != 1 and "s" or "")
            self.wait = math.ceil(wait)


class BaseException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Unexpected error")

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class NotFound(BaseException, Http404):
    """
    Exception used for not found objects.
    """

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Not found.")


class NotSupported(BaseException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = _("Method not supported for this endpoint.")


class BadRequest(BaseException):
    """
    Exception used on bad arguments detected
    on api view.
    """
    default_detail = _("Wrong arguments.")


class WrongArguments(BadRequest):
    """
    Exception used on bad arguments detected
    on service. This is same as `BadRequest`.
    """
    default_detail = _("Wrong arguments.")


class RequestValidationError(BadRequest):
    default_detail = _("Data validation error")


class PermissionDenied(PermissionDenied):
    """
    Compatibility subclass of restframework `PermissionDenied`
    exception.
    """
    pass


class IntegrityError(BadRequest):
    default_detail = _("Integrity Error for wrong or invalid arguments")


class PreconditionError(BadRequest):
    """
    Error raised on precondition method on viewset.
    """
    default_detail = _("Precondition error")


class Blocked(APIException):
    """
    Exception used on blocked accounts
    """
    status_code = 451
    default_detail = _("This account is currently blocked")


class NotEnoughSlotsForAccount(BaseException):
    """
    Exception used on import/edition/creation account errors where the user
    hasn't slots enough
    """
    default_detail = _("No room left for more accounts.")

    def __init__(self, is_private, total_memberships, detail=None):
        self.detail = detail or self.default_detail
        self.account_data = {
            "is_private": is_private,
            "total_memberships": total_memberships
        }


def format_exception(exc):
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, (dict, list, tuple,)):
            detail = exc.detail
        else:
            class_name = exc.__class__.__name__
            class_module = exc.__class__.__module__
            detail = {
                "_error_message": str(exc),
                "_error_type": "{0}.{1}".format(class_module, class_name)
            }
    else:
        detail = {
            "_error_message": str(exc),
            "_error_type": exc.__class__.__name__
        }
    return detail

def exception_handler(exc, context):
    headers = {}
    if isinstance(exc, APIException):
        if hasattr(exc, 'auth_header') and exc.auth_header:
            headers['WWW-Authenticate'] = exc.auth_header
        if hasattr(exc, 'wait') and exc.wait:
            headers['X-Throttle-Wait-Seconds'] = str(exc.wait)

        return response.Response(format_exception(exc), status=exc.status_code, headers=headers)

    elif isinstance(exc, DjangoValidationError):
        return response.Response({"_error_message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    elif isinstance(exc, Http404):
        return response.Response({'_error_message': str(exc)}, status=status.HTTP_404_NOT_FOUND)

    elif isinstance(exc, DjangoPermissionDenied):
        return response.Response({"_error_message": str(exc)}, status=status.HTTP_403_FORBIDDEN)

    # Handle any other unhandled exceptions
    return None
    # return response.Response({'_error_message': "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


ValidationError = DjangoValidationError
