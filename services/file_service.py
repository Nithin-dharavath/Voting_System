import logging
import os
import shutil
import uuid

from exceptions import FileError, ValidationError

logger = logging.getLogger(__name__)

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
    file_path = os.path.join("uploads", "profiles", filename)

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return f"/uploads/profiles/{filename}"
    except Exception as e:
        logger.error(f"Error saving profile picture for user {user_id}: {e}")
        raise FileError("Failed to save profile picture.")
