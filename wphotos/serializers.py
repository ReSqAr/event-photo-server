from django.contrib.auth.models import User
from rest_framework import serializers

from wphotos.models import Wedding, Photo, Comment


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'groups')


class WeddingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Wedding
        fields = ('url', 'name', 'description')


class PhotoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Photo
        fields = ('url', 'wedding', 'owner', 'dt', 'photo', 'thumbnail')


class CommentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Comment
        fields = ('url', 'owner', 'parent', 'photo', 'dt', 'text')
