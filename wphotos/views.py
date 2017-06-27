import string
from random import choice

from django.contrib.auth.models import User
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from wphotos.models import Photo, Upvote
from wphotos.permissions import IsOwnerOrReadOnly, IsUserOrReadOnly
from wphotos.serializers import UserSerializer, PhotoSerializer, UpvoteSerializer
from wserver.settings import LOCAL_NODE, CHALLENGE


@api_view(['GET'])
def server_information(request):
    return Response({"local_node": LOCAL_NODE})


@api_view(['POST'])
@permission_classes((AllowAny,))
def create_user(request):
    challenge = request.data['challenge']
    print("creating user: challenge = {}".format(challenge))

    normalise_challenge = lambda s: s.strip().lower()
    if normalise_challenge(challenge) != normalise_challenge(CHALLENGE):
        raise APIException("challenged failed")

    username = ''.join(choice(string.ascii_letters) for _ in range(24))
    password = ''.join(choice(string.ascii_letters) for _ in range(24))
    name = request.data['name']

    print("creating user: {}, pw: {}, name '{}'".format(username, password, name))

    user = User.objects.create_superuser(username=username, email='', password=password, first_name=name)

    token = user.auth_token.key

    return Response({"token": token})


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = (IsUserOrReadOnly,)

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class PhotoViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows photos to be viewed or edited.
    """
    permission_classes = (IsOwnerOrReadOnly,)

    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # https://stackoverflow.com/a/41112919/7729124
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class PhotoVisibleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows photos to be viewed or edited.
    """
    permission_classes = (IsOwnerOrReadOnly,)

    queryset = Photo.objects.filter(visible=True).all()
    serializer_class = PhotoSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # https://stackoverflow.com/a/41112919/7729124
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class UpvoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    permission_classes = (IsOwnerOrReadOnly,)

    queryset = Upvote.objects.all()
    serializer_class = UpvoteSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # https://stackoverflow.com/a/41112919/7729124
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
