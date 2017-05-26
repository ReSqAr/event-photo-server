import os

from PIL import Image
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import FileField
from io import BytesIO
from rest_framework import serializers

from wserver.settings import THUMBNAIL_SIZE


class Wedding(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)

    def __str__(self):
        return '{} ({})'.format(self.name,self.id)

class Photo(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    wedding = models.ForeignKey(Wedding, on_delete=models.CASCADE)
    dt = models.DateTimeField()
    photo = FileField(upload_to='photos')
    thumbnail = FileField(upload_to='thumbnail',null=True)

    def save(self, *args, **kwargs):

        # try to create a thumbnail
        self.make_thumbnail()

        super(Photo, self).save(*args, **kwargs)

    def make_thumbnail(self):
        """
        from: https://stackoverflow.com/a/43011898/7729124
        """
        image = Image.open(self.photo)
        image.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)

        thumb_name, thumb_extension = os.path.splitext(self.photo.name)
        thumb_extension = thumb_extension.lower()

        thumb_filename = thumb_name + '_thumbnail' + thumb_extension

        if thumb_extension in ['.jpg', '.jpeg']:
            FTYPE = 'JPEG'
        elif thumb_extension == '.gif':
            FTYPE = 'GIF'
        elif thumb_extension == '.png':
            FTYPE = 'PNG'
        else:
            return False  # Unrecognized file type

        # Save thumbnail to in-memory file as StringIO
        temp_thumb = BytesIO()
        image.save(temp_thumb, FTYPE)
        temp_thumb.seek(0)

        # set save=False, otherwise it will run in an infinite loop
        self.thumbnail.save(thumb_filename, ContentFile(temp_thumb.read()), save=False)
        temp_thumb.close()

        return True

    def __str__(self):
        return '{} ({})'.format(self.photo.name,self.id)


class Comment(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,null=True)
    dt = models.DateTimeField()
    text = models.CharField(max_length=200)

    def __str__(self):
        return '{} ({}): {}'.format(self.photo.photo.name,self.id,self.text)
