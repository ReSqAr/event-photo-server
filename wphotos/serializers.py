from django.contrib.auth.models import User
from rest_framework import serializers

from wphotos.models import Photo, Like, Event, AuthenticatedUserForEvent


class LikeSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.first_name')

    class Meta:
        model = Like
        fields = ('id', 'url', 'owner', 'owner_name', 'photo', 'dt',)
        read_only_fields = ('id', 'owner', 'dt',)

    def validate(self, data):
        user = self.context['request'].user
        event = data["photo"].event
        if not AuthenticatedUserForEvent.is_user_authenticated_for_event(user, event):
            raise serializers.ValidationError('user not authorised for this event')
        return data


class PhotoSerializer(serializers.ModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.first_name')
    comment = serializers.CharField(allow_blank=True)
    likes = serializers.IntegerField(source='like_set.count', read_only=True)
    liked_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = (
            'id', 'url', 'event', 'owner', 'owner_name',
            'upload_dt', 'photo_dt', 'visible', 'photo',
            'hash_md5', 'thumbnail', 'web_photo', 'comment',
            'likes', 'liked_by_current_user')
        read_only_fields = ('id', 'owner', 'thumbnail', 'web_photo', 'upload_dt', 'photo_dt')

    def validate(self, data):
        user = self.context['request'].user
        event = data["event"]
        if not AuthenticatedUserForEvent.is_user_authenticated_for_event(user, event):
            raise serializers.ValidationError('user not authorised for this event')
        return data

    def get_liked_by_current_user(self, obj):
        if not self.context['request'].user.is_authenticated():
            return False
        else:
            return Like.objects.filter(photo=obj, owner=self.context['request'].user).exists()


class UserAuthenticatedForEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthenticatedUserForEvent
        fields = ('id', 'url', 'user', 'event')


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('id', 'url', 'name', 'challenge', 'start_dt', 'end_dt', 'icon', 'dt')
        read_only_fields = ('id', 'dt')


class UserSerializer(serializers.ModelSerializer):
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'photos')
        depth = 1
