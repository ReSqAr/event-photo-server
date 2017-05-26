from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import viewsets

from wphotos.models import Wedding, Photo, Comment
from wphotos.serializers import UserSerializer, WeddingSerializer, PhotoSerializer, CommentSerializer


# Create your views here.


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class WeddingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows weddings to be viewed or edited.
    """
    queryset = Wedding.objects.all()
    serializer_class = WeddingSerializer


class PhotoViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows photos to be viewed or edited.
    """
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer


class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
