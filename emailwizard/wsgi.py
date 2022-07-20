"""
WSGI config for emailwizard project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emailwizard.settings")

from django.core.wsgi import get_wsgi_application   # noqa pylint: disable=wrong-import-position

application = get_wsgi_application()
