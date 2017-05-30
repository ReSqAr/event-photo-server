import os
from io import BytesIO
from typing import Tuple

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import FileField
from django.db.models.fields.files import FieldFile

from wserver.settings import THUMBNAIL_SIZE, WEB_PHOTO_SIZE


class Photo(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    dt = models.DateTimeField()
    photo = FileField(upload_to='photos')
    thumbnail = FileField(upload_to='thumbnail', null=True)
    web_photo = FileField(upload_to='web_photo', null=True)

    class Meta:
        ordering = ['-dt']

    def save(self, *args, **kwargs):

        # try to create a thumbnail
        self.save_scaled_version(source=self.photo, size=THUMBNAIL_SIZE, prefix='_thumbnail', target=self.thumbnail)

        # try to create a scaled version for web
        self.save_scaled_version(source=self.photo, size=WEB_PHOTO_SIZE, prefix='_web', target=self.web_photo)

        super(Photo, self).save(*args, **kwargs)

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
            FTYPE = 'JPEG'
        elif source_extension == '.gif':
            FTYPE = 'GIF'
        elif source_extension == '.png':
            FTYPE = 'PNG'
        else:
            return False  # Unrecognized file type

        # Save thumbnail to in-memory file as BytesIO
        temp_scaled = BytesIO()
        image.save(temp_scaled, FTYPE)
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
    text = models.CharField(max_length=200)

    class Meta:
        ordering = ['-dt']

    def __str__(self):
        return '{} ({}): {}'.format(self.photo.photo.name, self.id, self.text)
