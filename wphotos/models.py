import hashlib
import os
import datetime
from io import BytesIO
from typing import Tuple
import dateutil

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings
from django.db.models import FileField, BooleanField
from django.db.models.fields.files import FieldFile
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token

from wserver.settings import THUMBNAIL_SIZE, WEB_PHOTO_SIZE


# from: http://www.django-rest-framework.org/api-guide/authentication/
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Photo(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    dt = models.DateTimeField()
    visible = BooleanField(default=False)
    photo = FileField(upload_to='photos')
    hash_md5 = models.CharField(max_length=200)
    thumbnail = FileField(upload_to='thumbnail', null=True)
    web_photo = FileField(upload_to='web_photo', null=True)
    owner_comment = models.CharField(max_length=500,blank=True)

    class Meta:
        ordering = ['-dt']

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
            self.dt = dateutil.parser.parse(image._getexif()[36867])
        except:
            self.dt = datetime.datetime.now()

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


class Comment(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    dt = models.DateTimeField()
    text = models.CharField(max_length=500)

    class Meta:
        ordering = ['-dt']

    def __str__(self):
        return '{} ({}): {}'.format(self.photo.photo.name, self.id, self.text)
