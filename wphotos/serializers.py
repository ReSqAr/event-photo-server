from django.contrib.auth.models import User
from rest_framework import serializers

from wphotos.models import Photo, Comment


class CommentSerializer(serializers.HyperlinkedModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.first_name')

    class Meta:
        model = Comment
        fields = ('id', 'url', 'owner', 'owner_name', 'parent', 'photo', 'dt', 'text')
        read_only_fields = ('id', 'owner',)  # 'parent', 'photo',)


class PhotoSerializer(serializers.HyperlinkedModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    owner_name = serializers.ReadOnlyField(source='owner.first_name')
    owner_comment = serializers.CharField(allow_blank=True)

    class Meta:
        model = Photo
        fields = (
            'id', 'url', 'owner', 'owner_name',
            'upload_dt', 'photo_dt', 'visible', 'photo',
            'hash_md5', 'thumbnail', 'web_photo', 'owner_comment', 'comments')
        read_only_fields = ('id', 'owner', 'thumbnail', 'web_photo', 'upload_dt', 'photo_dt')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'photos')
        depth = 1
