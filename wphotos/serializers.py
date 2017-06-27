from django.contrib.auth.models import User
from rest_framework import serializers

from wphotos.models import Photo, Like, Event, AuthenticatedUserForEvent


class LikeSerializer(serializers.HyperlinkedModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.first_name')

    class Meta:
        model = Like
        fields = ('id', 'url', 'owner', 'owner_name', 'photo', 'dt',)
        read_only_fields = ('id', 'owner', 'dt',)


class RestrictedLikeSerializer(serializers.HyperlinkedModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.first_name')

    class Meta:
        model = Like
        fields = ('id', 'url', 'owner', 'owner_name', 'photo', 'dt',)
        read_only_fields = ('id', 'owner', 'dt',)


class PhotoSerializer(serializers.HyperlinkedModelSerializer):
    likes = LikeSerializer(many=True, read_only=True)
    owner_name = serializers.ReadOnlyField(source='owner.first_name')
    comment = serializers.CharField(allow_blank=True)
    likes_count = serializers.SerializerMethodField()
    liked_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = (
            'id', 'url', 'event', 'owner', 'owner_name',
            'upload_dt', 'photo_dt', 'visible', 'photo',
            'hash_md5', 'thumbnail', 'web_photo', 'comment',
            'likes', 'likes_count', 'likes_by_current_user')
        read_only_fields = ('id', 'owner', 'thumbnail', 'web_photo', 'upload_dt', 'photo_dt')

    @staticmethod
    def get_likes_count(obj):
        return obj.likes.count()

    def get_liked_by_current_user(self, obj):
        if not self.context['request'].user.is_authenticated():
            return False
        else:
            return Like.objects.filter(photo=obj, owner=self.context['request'].user).exists()


class RestrictedPhotoSerializer(serializers.HyperlinkedModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.first_name')
    comment = serializers.CharField(allow_blank=True)
    like_count = serializers.SerializerMethodField()
    liked_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = (
            'id', 'url', 'event', 'owner', 'owner_name',
            'upload_dt', 'photo_dt', 'visible', 'photo',
            'thumbnail', 'web_photo', 'comment',
            'likes_count', 'likes_by_current_user')
        read_only_fields = ('id', 'owner', 'thumbnail', 'web_photo', 'upload_dt', 'photo_dt')

    @staticmethod
    def get_likes_count(obj):
        return obj.likes.count()

    def get_liked_by_current_user(self, obj):
        if not self.context['request'].user.is_authenticated():
            return False
        else:
            return Like.objects.filter(photo=obj, owner=self.context['request'].user).exists()


class UserAuthenticatedForEventSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AuthenticatedUserForEvent
        fields = ('id', 'url', 'user', 'event')


class EventSerializer(serializers.HyperlinkedModelSerializer):
    authenticated_users = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ('id', 'url', 'name', 'start_dt', 'end_dt', 'icon', 'dt', 'authenticated_users')
        read_only_fields = ('id', 'dt')


class RestrictedEventSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'url', 'name')
        read_only_fields = ('id', 'name')


class UserSerializer(serializers.HyperlinkedModelSerializer):
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'photos')
        depth = 1
