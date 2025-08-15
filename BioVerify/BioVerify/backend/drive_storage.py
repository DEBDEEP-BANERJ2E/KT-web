"""
Google Drive integration for persistent model storage
"""

import os
import json
import pickle
import tempfile
from typing import Optional, Dict, List
from datetime import datetime
from config import config

try:
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("Google Drive API not available. Install google-api-python-client for Drive sync.")

class DriveStorageService:
    """Service for syncing models to Google Drive"""
    
    def __init__(self):
        self.enabled = config.GOOGLE_DRIVE_ENABLED and GOOGLE_AVAILABLE
        self.folder_id = config.GOOGLE_DRIVE_FOLDER_ID
        self.service = None
        
        if self.enabled:
            self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Drive service"""
        try:
            # OAuth 2.0 scopes
            SCOPES = ['https://www.googleapis.com/auth/drive']
            
            creds = None
            # Token file stores the user's access and refresh tokens
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # For production, you should set up service account credentials
                    print("Google Drive authentication required. Set up service account or run OAuth flow.")
                    self.enabled = False
                    return
                
                # Save the credentials for the next run
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            print("Google Drive service initialized")
            
        except Exception as e:
            print(f"Failed to initialize Google Drive service: {e}")
            self.enabled = False
    
    def create_folder_if_not_exists(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create folder in Drive if it doesn't exist"""
        if not self.enabled:
            return None
        
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.service.files().list(q=query).execute()
            items = results.get('files', [])
            
            if items:
                return items[0]['id']
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(body=folder_metadata).execute()
            return folder.get('id')
            
        except Exception as e:
            print(f"Error creating folder: {e}")
            return None
    
    def upload_file(self, local_path: str, drive_filename: str, folder_id: Optional[str] = None) -> Optional[str]:
        """Upload file to Google Drive"""
        if not self.enabled or not os.path.exists(local_path):
            return None
        
        try:
            file_metadata = {'name': drive_filename}
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            media = MediaFileUpload(local_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
            
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def download_file(self, file_id: str, local_path: str) -> bool:
        """Download file from Google Drive"""
        if not self.enabled:
            return False
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            with open(local_path, 'wb') as local_file:
                downloader = MediaIoBaseDownload(local_file, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            
            return True
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return False
    
    def sync_user_models(self, user_id: str) -> bool:
        """Sync user models to Google Drive"""
        if not self.enabled:
            return False
        
        try:
            # Create user folder
            user_folder_id = self.create_folder_if_not_exists(f"user_{user_id}", self.folder_id)
            if not user_folder_id:
                return False
            
            # Get model paths
            model_paths = config.get_model_paths(user_id)
            
            # Upload each model file
            for model_type, local_path in model_paths.items():
                if os.path.exists(local_path):
                    drive_filename = f"{user_id}_{model_type}.pkl"
                    file_id = self.upload_file(local_path, drive_filename, user_folder_id)
                    if file_id:
                        print(f"Uploaded {model_type} model for {user_id}")
            
            # Create sync metadata
            sync_metadata = {
                'user_id': user_id,
                'sync_timestamp': datetime.utcnow().isoformat(),
                'model_files': list(model_paths.keys())
            }
            
            # Save sync metadata
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(sync_metadata, f, indent=2)
                temp_path = f.name
            
            self.upload_file(temp_path, f"{user_id}_sync_metadata.json", user_folder_id)
            os.unlink(temp_path)
            
            return True
            
        except Exception as e:
            print(f"Error syncing models for {user_id}: {e}")
            return False
    
    def restore_user_models(self, user_id: str) -> bool:
        """Restore user models from Google Drive"""
        if not self.enabled:
            return False
        
        try:
            # Find user folder
            query = f"name='user_{user_id}' and mimeType='application/vnd.google-apps.folder'"
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            results = self.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if not folders:
                print(f"No Drive folder found for user {user_id}")
                return False
            
            user_folder_id = folders[0]['id']
            
            # Get model paths
            model_paths = config.get_model_paths(user_id)
            
            # Download each model file
            for model_type, local_path in model_paths.items():
                drive_filename = f"{user_id}_{model_type}.pkl"
                
                # Search for the file
                file_query = f"name='{drive_filename}' and '{user_folder_id}' in parents"
                file_results = self.service.files().list(q=file_query).execute()
                files = file_results.get('files', [])
                
                if files:
                    file_id = files[0]['id']
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)
                    
                    # Download file
                    if self.download_file(file_id, local_path):
                        print(f"Restored {model_type} model for {user_id}")
            
            return True
            
        except Exception as e:
            print(f"Error restoring models for {user_id}: {e}")
            return False
    
    def list_user_backups(self) -> List[Dict]:
        """List all user model backups in Drive"""
        if not self.enabled:
            return []
        
        try:
            # Get all user folders
            query = f"name contains 'user_' and mimeType='application/vnd.google-apps.folder'"
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            results = self.service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            backups = []
            for folder in folders:
                user_id = folder['name'].replace('user_', '')
                
                # Get sync metadata if available
                metadata_query = f"name='{user_id}_sync_metadata.json' and '{folder['id']}' in parents"
                metadata_results = self.service.files().list(q=metadata_query).execute()
                metadata_files = metadata_results.get('files', [])
                
                backup_info = {
                    'user_id': user_id,
                    'folder_id': folder['id'],
                    'created_time': folder.get('createdTime'),
                    'modified_time': folder.get('modifiedTime')
                }
                
                if metadata_files:
                    # Download and parse metadata
                    with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as f:
                        if self.download_file(metadata_files[0]['id'], f.name):
                            with open(f.name, 'r') as meta_file:
                                metadata = json.load(meta_file)
                                backup_info.update(metadata)
                
                backups.append(backup_info)
            
            return backups
            
        except Exception as e:
            print(f"Error listing backups: {e}")
            return []

# Global drive service instance
drive_service = DriveStorageService()
