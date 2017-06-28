import hashlib
import string
from random import choice

from django.contrib.auth.models import User
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from wphotos.models import Photo, Like, Event, AuthenticatedUserForEvent
from wphotos.permissions import IsUserOrAdminConstructor, IsOwnerOrAuthorisedForEventConstructor
from wphotos.serializers import UserSerializer, PhotoSerializer, LikeSerializer, EventSerializer, \
    RestrictedEventSerializer


@api_view(['POST'])
@permission_classes((AllowAny,))
def create_user(request):
    name = request.data['name'].strip()

    if len(name) < 3:
        raise ValidationError("user name too short")

    username = ''.join(choice(string.ascii_letters) for _ in range(24))
    password = ''.join(choice(string.ascii_letters) for _ in range(24))

    print("creating user: {}, pw: {}, name '{}'".format(username, password, name))

    user = User.objects.create_superuser(username=username, email='', password=password, first_name=name)

    token = user.auth_token.key

    return Response({"token": token}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def authenticate_user_for_event(request, **kwargs):
    user = request.user
    event_id = kwargs['event_id']
    hashed_challenge = request.data['hashed_challenge']
    print("authenticating: user = {}, event id = {}, hashed challenge = {}".format(user.id, event_id, hashed_challenge))

    event_id = int(event_id)

    try:
        event = Event.objects.get(pk=event_id)
    except:
        raise ValidationError("challenged failed")

    challenge_for_user = "{username}${token}${challenge}".format(
        username=user.first_name,
        token=user.auth_token.key,
        challenge=event.challenge.strip().lower()
    )

    expected_challenge = hashlib.md5(challenge_for_user.encode('utf8')).hexdigest()
    print("expected challenge = {}".format(expected_challenge))

    if hashed_challenge != expected_challenge:
        raise ValidationError("challenged failed")

    AuthenticatedUserForEvent.objects.create(user=user, event=event)

    return Response(RestrictedEventSerializer(event, context={'request': request}).data,
                    status=status.HTTP_201_CREATED)


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
    API endpoint that allows photos associated to an event to be viewed or edited.
    """
    permission_classes = (IsOwnerOrAuthorisedForEventConstructor(lambda x: x.owner, lambda x: x.event),)

    serializer_class = PhotoSerializer

    def get_queryset(self):
        # setup queryset
        queryset = Photo.objects

        # get metadata from the request object
        user = self.request.user
        event_id = self.request.query_params.get('event_id', None)
        only_visible = self.request.query_params.get('only_visible', None)

        # only show visible photos
        if only_visible is not None:
            if only_visible == "1" or only_visible.lower() == "true":
                queryset = queryset.filter(visible=True)

        # if there is an event id, use it to filter the queryset
        if event_id is not None:
            event = Event.objects.get(pk=event_id)

            if AuthenticatedUserForEvent.is_user_authenticated_for_event(user, event):
                return queryset.filter(event=event).all()
            else:
                return []
        # if we have the super user, they can see everything
        elif user.is_superuser:
            return queryset.all()
        # a unprivileged user may only view photos they are authorised to see
        else:
            # careful: don't split this query up in two filter statements
            queryset = queryset.filter(event__authenticated_users__isnull=False,
                                       event__authenticated_users__user__id=user.id)
            return queryset.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LikeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    permission_classes = (IsOwnerOrAuthorisedForEventConstructor(lambda x: x.owner, lambda x: x.photo.event),)

    serializer_class = LikeSerializer

    def get_queryset(self):
        # setup queryset
        queryset = Like.objects

        # get metadata from the request object
        user = self.request.user
        event_id = self.request.query_params.get('event_id', None)
        only_visible = self.request.query_params.get('only_visible', None)

        # only show visible photos
        if only_visible is not None:
            if only_visible == "1" or only_visible.lower() == "true":
                queryset = queryset.filter(photo__visible=True)

        # if there is an event id, use it to filter the queryset
        if event_id is not None:
            event = Event.objects.get(pk=event_id)

            if AuthenticatedUserForEvent.is_user_authenticated_for_event(user, event):
                return queryset.filter(photo__event=event).all()
            else:
                return []
        # if we have the super user, they can see everything
        elif user.is_superuser:
            return queryset.all()
        # a unprivileged user may only view photos they are authorised to see
        else:
            # careful: don't split this query up in two filter statements
            queryset = queryset.filter(photo__event__authenticated_users__isnull=False,
                                       photo__event__authenticated_users__user__id=user.id)
            return queryset.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
