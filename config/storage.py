"""Stores uploaded files (book covers, donation photos) on Cloudinary instead of the server's disk.

Render's free plan wipes its disk on every restart, so files kept there would be lost.
Files are uploaded as-is ("raw"), after BookLoop has already checked, resized and
stripped them, and each gets a random suffix so its address cannot be guessed.
"""
import os
import uuid

import cloudinary
import cloudinary.uploader
import cloudinary.utils
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class CloudinaryMediaStorage(Storage):
    resource_type = "raw"

    def get_available_name(self, name, max_length=None):
        folder, filename = os.path.split(name)
        stem, ext = os.path.splitext(filename)
        unique = f"{stem}-{uuid.uuid4().hex[:12]}{ext}"
        return f"{folder}/{unique}" if folder else unique

    def _save(self, name, content):
        content.seek(0)
        cloudinary.uploader.upload(
            content, public_id=name, resource_type=self.resource_type,
            overwrite=False, use_filename=False, unique_filename=False,
        )
        return name

    def url(self, name):
        return cloudinary.utils.cloudinary_url(name, resource_type=self.resource_type, secure=True)[0]

    def _open(self, name, mode="rb"):
        response = requests.get(self.url(name), timeout=20)
        response.raise_for_status()
        file = ContentFile(response.content)
        file.name = name
        return file

    def exists(self, name):
        return False  # every name gets a random suffix, so it is always new

    def delete(self, name):
        if name:
            cloudinary.uploader.destroy(name, resource_type=self.resource_type, invalidate=True)

    def size(self, name):
        return len(self._open(name).read())
