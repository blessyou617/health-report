import os
import uuid
import aiofiles
from datetime import datetime
from fastapi import UploadFile
from app.core.config import settings


class FileService:
    """File upload and storage service"""
    
    ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
    ALLOWED_MIME_TYPES = [
        "application/pdf",
        "image/jpeg", 
        "image/png"
    ]
    
    @staticmethod
    async def save_file(file: UploadFile) -> dict:
        """
        Save uploaded file and return file info
        """
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in FileService.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type not allowed. Allowed: {FileService.ALLOWED_EXTENSIONS}")
        
        if file.content_type not in FileService.ALLOWED_MIME_TYPES:
            raise ValueError(f"Invalid file content type: {file.content_type}")
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d")
        unique_id = uuid.uuid4().hex[:8]
        new_filename = f"{timestamp}_{unique_id}{file_ext}"
        
        # Create upload directory
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, new_filename)
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        # Get file size
        file_size = len(content)
        
        # Return file info
        return {
            "filename": new_filename,
            "original_filename": file.filename,
            "file_type": file_ext[1:],  # remove dot
            "file_path": file_path,
            "file_url": f"/uploads/{new_filename}",
            "file_size": file_size
        }
    
    @staticmethod
    async def delete_file(file_path: str):
        """Delete file from storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")


file_service = FileService()
