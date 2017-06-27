import datetime
import hashlib
import os
from io import BytesIO
from typing import Tuple

import dateutil.parser
from PIL import Image
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import FileField, BooleanField
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError

from wserver.settings import THUMBNAIL_SIZE, WEB_PHOTO_SIZE


# from: http://www.django-rest-framework.org/api-guide/authentication/
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Event(models.Model):
    name = models.CharField(max_length=200)
    start_dt = models.DateTimeField()
    end_dt = models.DateTimeField()
    dt = models.DateTimeField()
    challenge = models.CharField(max_length=200)
    icon = FileField(upload_to='event_icon', null=True)

    class Meta:
        ordering = ['-start_dt']

    def save(self, *args, **kwargs):
        # set dt
        self.dt = datetime.datetime.now()

        super(Event, self).save(*args, **kwargs)

    def __str__(self):
        return '{} - {}'.format(self.id, self.name)


class AuthenticatedUserForEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authenticated_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='authenticated_users')
    dt = models.DateTimeField()

    class Meta:
        ordering = ['-dt']

    def save(self, *args, **kwargs):
        # set dt
        self.dt = datetime.datetime.now()

        super(AuthenticatedUserForEvent, self).save(*args, **kwargs)

    def __str__(self):
        return '{}: {} - {}'.format(self.id, self.event.name, self.user.name)

    @staticmethod
    def is_user_authenticated_for_event(user, event):
        return AuthenticatedUserForEvent.objects.filter(user=user, event=event).exists()


class Photo(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos')

    # TODO: validate that owner is authorised to write to event!

    upload_dt = models.DateTimeField()
    photo_dt = models.DateTimeField()
    visible = BooleanField(default=False)

    photo = FileField(upload_to='photos')
    hash_md5 = models.CharField(max_length=200)
    thumbnail = FileField(upload_to='thumbnail', null=True)
    web_photo = FileField(upload_to='web_photo', null=True)

    comment = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['-upload_dt']

    def save(self, *args, **kwargs):
        # check md5sum
        self.photo.seek(0)
        local_md5 = self.compute_md5(self.photo)
        if self.hash_md5.strip() != local_md5:
            raise ValidationError('md5 mismatch: {} != {}'.format(self.hash_md5, local_md5))
        self.photo.seek(0)

        # try to create a thumbnail
        self.save_scaled_version(source=self.photo, size=THUMBNAIL_SIZE, prefix='_thumbnail', target=self.thumbnail)

        # try to create a scaled version for web
        self.save_scaled_version(source=self.photo, size=WEB_PHOTO_SIZE, prefix='_web', target=self.web_photo)

        # find creation date
        image = Image.open(self.photo)
        try:
            # format of dt_str: 2017:06:14 18:35:33
            dt_str = image._getexif()[36867]
            dt_str = dt_str.replace(':', '-', 2)
            self.photo_dt = dateutil.parser.parse(dt_str)
        except:
            self.photo_dt = datetime.datetime.now()

        # upload dt
        self.upload_dt = datetime.datetime.now()

        super(Photo, self).save(*args, **kwargs)

    @staticmethod
    def compute_md5(f: FileField) -> str:
        hash_md5 = hashlib.md5()
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def save_scaled_version(source: FieldFile, size: Tuple[int, int], prefix: str, target: FieldFile) -> bool:
        """
        from: https://stackoverflow.com/a/43011898/7729124
        """
        image = Image.open(source)
        image.thumbnail(size, Image.ANTIALIAS)

        source_name, source_extension = os.path.splitext(source.name)
        source_extension = source_extension.lower()
        scaled_filename = source_name + prefix + source_extension

        if source_extension in ['.jpg', '.jpeg']:
            file_type = 'JPEG'
        elif source_extension == '.gif':
            file_type = 'GIF'
        elif source_extension == '.png':
            file_type = 'PNG'
        else:
            return False  # Unrecognized file type

        # Save thumbnail to in-memory file as BytesIO
        temp_scaled = BytesIO()
        image.save(temp_scaled, file_type)
        temp_scaled.seek(0)

        # set save=False, otherwise it will run in an infinite loop
        target.save(scaled_filename, ContentFile(temp_scaled.read()), save=False)
        temp_scaled.close()

        return True

    def __str__(self):
        return '{} ({})'.format(self.photo.name, self.id)


class Like(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='likes')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    dt = models.DateTimeField()

    # TODO: validate that owner is authorised to write to event!

    class Meta:
        unique_together = ('photo', 'owner')
        ordering = ['-dt']

    def save(self, *args, **kwargs):
        # set dt
        self.dt = datetime.datetime.now()

        super(Like, self).save(*args, **kwargs)

    def __str__(self):
        return '{} ({})'.format(self.photo.photo.name, self.id)
