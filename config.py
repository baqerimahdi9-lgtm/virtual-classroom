"""
تنظیمات پروژه
"""
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'my-secret-key-2024-change-me'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = 'static/uploads'
    VIDEO_FOLDER = 'static/uploads/videos'
    FILE_FOLDER = 'static/uploads/files'
    
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
    
    ALLOWED_FILE_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'ppt', 'pptx',
        'zip', 'rar', '7z',
        'png', 'jpg', 'jpeg', 'gif', 'webp',
        'txt', 'csv', 'xlsx', 'xls'
    }
    
    ALLOWED_VIDEO_EXTENSIONS = {
        'mp4', 'webm', 'avi', 'mkv', 'mov'
    }