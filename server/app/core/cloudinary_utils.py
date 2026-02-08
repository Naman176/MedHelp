import cloudinary
import cloudinary.uploader
from app.core.config import settings

# Configure Cloudinary
cloudinary.config( 
  cloud_name = settings.CLOUDINARY_CLOUD_NAME, 
  api_key = settings.CLOUDINARY_API_KEY, 
  api_secret = settings.CLOUDINARY_API_SECRET 
)

def upload_file(file, folder: str = "medhelp_degrees"):
    """
    Uploads a file to Cloudinary and returns the secure URL.
    """
    try:
        # Upload the file
        response = cloudinary.uploader.upload(file.file, folder=folder, resource_type="auto")
        return response["secure_url"]
    except Exception as e:
        print(f"Error uploading to Cloudinary: {e}")
        return None