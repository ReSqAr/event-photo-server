from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from wphotos.models import Photo, Comment
from wphotos.permissions import IsOwnerOrReadOnly, IsUserOrReadOnly
from wphotos.serializers import UserSerializer, PhotoSerializer, CommentSerializer
from wserver.settings import LOCAL_NODE


@api_view(['GET'])
def server_information(request):
    return Response({"local_node": LOCAL_NODE})

@api_view(['POST'])
def create_user(request):
    request.
    return Response({"local_node": LOCAL_NODE})


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

class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    permission_classes = (IsOwnerOrReadOnly,)

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # https://stackoverflow.com/a/41112919/7729124
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

