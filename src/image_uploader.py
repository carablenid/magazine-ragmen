import os
import cloudinary
import cloudinary.uploader


def _configure():
    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def upload_image(local_path: str) -> str:
    _configure()
    result = cloudinary.uploader.upload(
        local_path,
        folder="magazine-ragmen",
        resource_type="image",
        quality="auto:good",
    )
    return result["secure_url"]
