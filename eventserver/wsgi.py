"""
WSGI config for wserver project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# sudo apt-get install python3-dev libjpeg8-dev
# pip3 install django djangorestframework typing Pillow python-dateutil

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventserver.settings")

application = get_wsgi_application()
