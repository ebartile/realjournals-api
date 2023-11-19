# -*- coding: utf-8 -*-
import contextlib

from django.conf import settings
from django.test.client import RequestFactory as DjangoRequestFactory
from django.utils.encoding import force_bytes
from django.utils.http import urlencode

from rest_framework.auth.settings import api_settings
from rest_framework.api import renderers


@contextlib.contextmanager
def override_api_settings(**settings):
    old_settings = {}

    for k, v in settings.items():
        # Save settings
        try:
            old_settings[k] = api_settings.user_settings[k]
        except KeyError:
            pass

        # Install temporary settings
        api_settings.user_settings[k] = v

        # Delete any cached settings
        try:
            delattr(api_settings, k)
        except AttributeError:
            pass

    yield

    for k in settings.keys():
        # Delete temporary settings
        api_settings.user_settings.pop(k)

        # Restore saved settings
        try:
            api_settings.user_settings[k] = old_settings[k]
        except KeyError:
            pass

        # Delete any cached settings
        try:
            delattr(api_settings, k)
        except AttributeError:
            pass


class APIRequestFactory(DjangoRequestFactory):
    renderer_classes_list = [
        renderers.MultiPartRenderer,
        renderers.JSONRenderer
    ]
    default_format = "multipart"

    def __init__(self, enforce_csrf_checks=False, **defaults):
        self.enforce_csrf_checks = enforce_csrf_checks
        self.renderer_classes = {}
        for cls in self.renderer_classes_list:
            self.renderer_classes[cls.format] = cls
        super().__init__(**defaults)

    def _encode_data(self, data, format=None, content_type=None):
        """
        Encode the data returning a two tuple of (bytes, content_type)
        """

        if data is None:
            return ('', content_type)

        assert format is None or content_type is None, (
            'You may not set both `format` and `content_type`.'
        )

        if content_type:
            # Content type specified explicitly, treat data as a raw bytestring
            ret = force_bytes(data, settings.DEFAULT_CHARSET)

        else:
            format = format or self.default_format

            assert format in self.renderer_classes, (
                "Invalid format '{}'. Available formats are {}. "
                "Set TEST_REQUEST_RENDERER_CLASSES to enable "
                "extra request formats.".format(
                    format,
                    ', '.join(["'" + fmt + "'" for fmt in self.renderer_classes])
                )
            )

            # Use format and render the data into a bytestring
            renderer = self.renderer_classes[format]()
            ret = renderer.render(data)

            # Determine the content-type header from the renderer
            content_type = renderer.media_type
            if renderer.charset:
                content_type = "{}; charset={}".format(
                    content_type, renderer.charset
                )

            # Coerce text to bytes if required.
            if isinstance(ret, str):
                ret = ret.encode(renderer.charset)

        return ret, content_type

    def get(self, path, data=None, **extra):
        r = {
            'QUERY_STRING': urlencode(data or {}, doseq=True),
        }
        if not data and '?' in path:
            # Fix to support old behavior where you have the arguments in the
            # url. See #1461.
            query_string = force_bytes(path.split('?')[1])
            query_string = query_string.decode('iso-8859-1')
            r['QUERY_STRING'] = query_string
        r.update(extra)
        return self.generic('GET', path, **r)

    def post(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('POST', path, data, content_type, **extra)

    def put(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('PUT', path, data, content_type, **extra)

    def patch(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('PATCH', path, data, content_type, **extra)

    def delete(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('DELETE', path, data, content_type, **extra)

    def options(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('OPTIONS', path, data, content_type, **extra)

    def generic(self, method, path, data='',
                content_type='application/octet-stream', secure=False, **extra):
        # Include the CONTENT_TYPE, regardless of whether or not data is empty.
        if content_type is not None:
            extra['CONTENT_TYPE'] = str(content_type)

        return super().generic(
            method, path, data, content_type, secure, **extra)

    def request(self, **kwargs):
        request = super().request(**kwargs)
        request._dont_enforce_csrf_checks = not self.enforce_csrf_checks
        return request
