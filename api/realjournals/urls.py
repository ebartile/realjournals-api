from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls import include
from django.views.decorators.cache import never_cache
from apps.utils.api import MyJavaScriptView
from .routers import router

urlpatterns = [
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('api-auth/', include('rest_framework.urls')),
    path('v1/', include(router.urls)),
    path('admin/', admin.site.urls),
    path('myjs/', MyJavaScriptView.as_view()),
]


##############################################
# Front sitemap
##############################################

if settings.FRONT_SITEMAP_ENABLED:
    from django.contrib.sitemaps.views import index
    from django.contrib.sitemaps.views import sitemap
    from django.views.decorators.cache import cache_page

    from apps.sitemaps import sitemaps

    urlpatterns += [
        re_path(r"^front/sitemap\.xml$",
            cache_page(settings.FRONT_SITEMAP_CACHE_TIMEOUT)(index),
            {"sitemaps": sitemaps, 'sitemap_url_name': 'front-sitemap'},
            name="front-sitemap-index"),
        re_path(r"^front/sitemap-(?P<section>.+)\.xml$",
            cache_page(settings.FRONT_SITEMAP_CACHE_TIMEOUT)(sitemap),
            {"sitemaps": sitemaps},
            name="front-sitemap")
    ]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    def mediafiles_urlpatterns(prefix):
        """
        Method for serve media files with runserver.
        """
        import re
        from django.views.static import serve

        return [
            re_path(r'^%s(?P<path>.*)$' % re.escape(prefix.lstrip('/')), serve,
                {'document_root': settings.MEDIA_ROOT})
        ]

    # Hardcoded only for development server
    urlpatterns += staticfiles_urlpatterns(prefix="/static/")
    urlpatterns += mediafiles_urlpatterns(prefix="/media/")
