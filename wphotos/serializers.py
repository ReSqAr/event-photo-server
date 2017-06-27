from django.contrib.auth.models import User
from rest_framework import serializers

from wphotos.models import Photo, Upvote


class UpvoteSerializer(serializers.HyperlinkedModelSerializer):
    owner_name = serializers.ReadOnlyField(source='owner.first_name')

    class Meta:
        model = Upvote
        fields = ('id', 'url', 'owner', 'owner_name', 'photo', 'dt',)
        read_only_fields = ('id', 'owner', 'dt',)


class PhotoSerializer(serializers.HyperlinkedModelSerializer):
    upvotes = UpvoteSerializer(many=True, read_only=True)
    owner_name = serializers.ReadOnlyField(source='owner.first_name')
    owner_comment = serializers.CharField(allow_blank=True)
    upvote_count = serializers.SerializerMethodField()
    upvoted_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Photo
        fields = (
            'id', 'url', 'owner', 'owner_name',
            'upload_dt', 'photo_dt', 'visible', 'photo',
            'hash_md5', 'thumbnail', 'web_photo', 'owner_comment',
            'upvotes', 'upvote_count', 'upvoted_by_current_user')
        read_only_fields = ('id', 'owner', 'thumbnail', 'web_photo', 'upload_dt', 'photo_dt')

    @staticmethod
    def get_upvote_count(obj):
        return obj.upvotes.count()

    def get_upvoted_by_current_user(self, obj):
        if not self.context['request'].user.is_authenticated():
            return False
        else:
            return Upvote.objects.filter(photo=obj, owner=self.context['request'].user).exists()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    photos = PhotoSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'photos')
        depth = 1
