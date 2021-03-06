"""wserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from rest_framework import routers

from eventphotos import views
from eventserver import settings

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'authenticateduserforevent', views.AuthenticatedUserForEventViewSet)
router.register(r'events', views.EventViewSet, base_name='event')
router.register(r'photos', views.PhotoViewSet, base_name='photo')
router.register(r'likes', views.LikeViewSet, base_name='like')


urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^api/create-user/', views.create_user, name='create-user'),
    url(r'^api/authenticate_user_for_event/(?P<event_id>\d+)', views.authenticate_user_for_event,
        name='auth-user-for-event'),
    url(r'^api/events-metadata/', views.events_metadata, name='events-metadata'),
    url(r'^api/single-event-metadata/(?P<event_id>\d+)', views.single_event_metadata, name='single-event-metadata'),
    url(r'^api/like-photo/', views.like_photo, name='like-photo'),

    url(r'^api/', include(router.urls)),

    url(r'^api/auth/', include('rest_framework.urls', namespace='rest_framework')),
    # url(r'^api/token-auth/', rest_views.obtain_auth_token),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
