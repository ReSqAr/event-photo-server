import hashlib
import string
from random import choice

from django.contrib.auth.models import User
from rest_framework import viewsets, mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from wphotos.models import Photo, Like, Event, AuthenticatedUserForEvent
from wphotos.permissions import IsUserOrAdminConstructor, IsOwnerOrAuthorisedForEventConstructor
from wphotos.serializers import UserSerializer, PhotoSerializer, LikeSerializer, EventSerializer, \
    RestrictedEventSerializer, RestrictedPhotoSerializer


@api_view(['POST'])
@permission_classes((AllowAny,))
def create_user(request):
    name = request.data['name'].strip()

    if len(name) < 3:
        raise APIException("user name too short")

    username = ''.join(choice(string.ascii_letters) for _ in range(24))
    password = ''.join(choice(string.ascii_letters) for _ in range(24))

    print("creating user: {}, pw: {}, name '{}'".format(username, password, name))

    user = User.objects.create_superuser(username=username, email='', password=password, first_name=name)

    token = user.auth_token.key

    return Response({"token": token})


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def authenticate_user(request):
    user = request.user
    event_id = request.data['event_id']
    hashed_challenge = request.data['hashed_challenge']
    print("authenticating: user = {}, event id = {}, hashed challenge = {}".format(user.id, event_id, hashed_challenge))

    event_id = int(event_id)

    try:
        event = Event.objects.get(pk=event_id)
    except:
        raise APIException("challenged failed")

    challenge_for_user = "{username}${token}${challenge}".format(
        username=user.first_name,
        token=user.auth_token.key,
        challenge=event.challenge.strip().lower()
    )

    expected_challenge = hashlib.md5(challenge_for_user).hexdigest()
    print("expected challenge = {}".format(expected_challenge))

    if hashed_challenge != expected_challenge:
        raise APIException("challenged failed")

    AuthenticatedUserForEvent.objects.create(user=user, event=event)

    return Response(EventSerializer(event).data)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = (IsUserOrAdminConstructor(lambda x: x),)

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """
    permission_classes = (IsAdminUser,)

    queryset = Event.objects.all()
    serializer_class = EventSerializer


class RestrictedEventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows event names to be viewed.
    """
    permission_classes = (IsAuthenticated,)

    queryset = Event.objects.all()
    serializer_class = RestrictedEventSerializer


class PhotoViewSet(viewsets.ModelViewSet, mixins.UpdateModelMixin):
    """
    API endpoint that allows photos to be viewed or edited.
    """
    permission_classes = (IsAdminUser,)

    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RestrictedPhotoViewSet(viewsets.ModelViewSet, mixins.UpdateModelMixin):
    """
    API endpoint that allows photos associated to an event to be viewed or edited.
    """
    permission_classes = (IsOwnerOrAuthorisedForEventConstructor(lambda x: x.owner, lambda x: x.event),)

    serializer_class = RestrictedPhotoSerializer

    def get_queryset(self):
        event_id = int(self.kwargs['event_id'])
        event = Event.objects.get(pk=event_id)
        user = self.request.user

        if AuthenticatedUserForEvent.is_user_authenticated_for_event(user, event):
            return Photo.objects.filter(event=event, visible=True).all()
        else:
            return None

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LikeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    permission_classes = (IsAdminUser,)

    queryset = Like.objects.all()
    serializer_class = LikeSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RestrictedLikeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    permission_classes = (IsOwnerOrAuthorisedForEventConstructor(lambda x: x.owner, lambda x: x.photo.event),)

    serializer_class = LikeSerializer

    def get_queryset(self):
        event_id = int(self.kwargs['event_id'])
        event = Event.objects.get(pk=event_id)
        user = self.request.user

        if AuthenticatedUserForEvent.is_user_authenticated_for_event(user, event):
            return Like.objects.filter(photo__event=event, photo__visible=True).all()
        else:
            return None

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
