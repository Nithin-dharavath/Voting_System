import logging
import os
import shutil
import uuid

import boto3

from config import settings
from exceptions import FileError, ValidationError

logger = logging.getLogger(__name__)


class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client("s3", region_name=settings.s3_region)
        self.bucket = settings.s3_bucket

    def upload_fileobj(self, file_obj, key: str) -> str:
        self.s3_client.upload_fileobj(file_obj, self.bucket, key)
        return f"https://{self.bucket}.s3.{settings.s3_region}.amazonaws.com/{key}"

    def get_file_url(self, key: str) -> str:
        return f"https://{self.bucket}.s3.{settings.s3_region}.amazonaws.com/{key}"


_s3_storage: S3Storage | None = None


def _get_storage() -> S3Storage | None:
    global _s3_storage
    if settings.environment == "production":
        if _s3_storage is None:
            _s3_storage = S3Storage()
        return _s3_storage
    return None


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_and_save_verification_file(user_id: int, election_id: int, v_type: str, file) -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError("Invalid file format. Please upload a JPG, JPEG, or PNG image.")

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValidationError("File size exceeds the 5 MB limit.")

    try:
        import io

        from PIL import Image

        contents = file.file.read()
        img = Image.open(io.BytesIO(contents))
        img.verify()
        file.file = io.BytesIO(contents)
    except Exception:
        raise ValidationError("Invalid or corrupted image file.")

    folder = "selfies" if v_type == "SELFIE" else "signatures"
    filename = f"verify_{election_id}_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    key = f"uploads/{folder}/{filename}"

    storage = _get_storage()
    if storage:
        try:
            file.file.seek(0)
            return storage.upload_fileobj(file.file, key)
        except Exception as e:
            logger.error(f"Error uploading verification file to S3 for user {user_id}: {e}")
            raise FileError("Failed to upload verification file.")

    file_path = os.path.join("uploads", folder, filename)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return f"/uploads/{folder}/{filename}"
    except Exception as e:
        logger.error(f"Error saving verification file for user {user_id}: {e}")
        raise FileError("Failed to save verification file.")


def validate_and_save_profile_picture(user_id: int, file) -> str | None:
    if not file or not file.filename:
        return None

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError("Invalid file format. Please upload a JPG, JPEG, or PNG image.")

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValidationError("File size exceeds the 5 MB limit.")

    try:
        import io

        from PIL import Image

        contents = file.file.read()
        img = Image.open(io.BytesIO(contents))
        img.verify()
        file.file = io.BytesIO(contents)
    except Exception:
        raise ValidationError("Invalid or corrupted image file.")

    filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    key = f"uploads/profiles/{filename}"

    storage = _get_storage()
    if storage:
        try:
            file.file.seek(0)
            return storage.upload_fileobj(file.file, key)
        except Exception as e:
            logger.error(f"Error uploading profile picture to S3 for user {user_id}: {e}")
            raise FileError("Failed to upload profile picture.")

    file_path = os.path.join("uploads", "profiles", filename)
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return f"/uploads/profiles/{filename}"
    except Exception as e:
        logger.error(f"Error saving profile picture for user {user_id}: {e}")
        raise FileError("Failed to save profile picture.")
