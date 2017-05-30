from django.contrib.auth.models import User
from rest_framework import serializers

from wphotos.models import Photo, Comment


class CommentSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    owner_name = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Comment
        fields = ('url', 'owner', 'owner_name', 'parent', 'photo', 'dt', 'text')
        read_only_fields = ('owner', )


class PhotoSerializer(serializers.HyperlinkedModelSerializer):
    comments = CommentSerializer(many=True,read_only=True)
    owner_name = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Photo
        fields = ('url', 'owner', 'owner_name', 'dt', 'photo', 'thumbnail', 'web_photo', 'comments')
        read_only_fields = ('owner', 'thumbnail', 'web_photo')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    photos = PhotoSerializer(many=True,read_only=True)

    class Meta:
        model = User
        fields = ('url', 'username', 'photos')
        depth = 1
