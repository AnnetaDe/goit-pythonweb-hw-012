import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


def upload_avatar(file, public_id):
    result = cloudinary.uploader.upload(
        file,
        public_id=f"avatars/{public_id}",
        overwrite=True,
        folder="avatars"
    )
    return result.get("secure_url")
