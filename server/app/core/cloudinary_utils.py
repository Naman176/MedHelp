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
    

def delete_file(image_url: str):
    """
    Deletes a file from Cloudinary using its secure URL.
    Extracts the folder and file name to create the exact public_id Cloudinary needs.
    """
    if not image_url:
        return

    try:
        # Example URL: https://res.cloudinary.com/cloud_name/image/upload/v1234/medhelp_profiles/my_pic.jpg
        parts = image_url.split('/')
        
        # Get the file name without the extension (e.g., 'my_pic' from 'my_pic.jpg')
        file_name = parts[-1].split('.')[0]
        
        # Get the folder name (e.g., 'medhelp_profiles')
        folder_name = parts[-2]
        
        # Combine them to get the Cloudinary public_id: "medhelp_profiles/my_pic"
        public_id = f"{folder_name}/{file_name}"
        
        # Tell Cloudinary to delete it permanently
        cloudinary.uploader.destroy(public_id)
        print(f"Successfully deleted {public_id} from Cloudinary.")
        
    except Exception as e:
        print(f"Error deleting from Cloudinary: {e}")