import os
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']

class CloudService:
    def __init__(self, credentials_path='credentials.json', token_path='token.pickle'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.creds = None
        self.is_mock = False

    def authenticate(self):
        """Authenticates with Google Drive API."""
        if not os.path.exists(self.credentials_path):
            print("Credentials not found. Running in MOCK mode.")
            self.is_mock = True
            return False

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                # We can't run console based flow in headless backend usually, 
                # but for this tasks' context we might need to assume a setup flow or return auth URL.
                # For now, we'll try standard flow which opens browser on server if possible, 
                # or we might need to implement a detailed auth flow via API.
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"Authentication failed: {e}")
                    return False

            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.creds = creds
        try:
            self.service = build('drive', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"Failed to build service: {e}")
            return False

    def list_files(self, page_size=100, query=None):
        if self.is_mock:
            return [
                {'id': '1', 'name': 'Mock_Invoice_2023.pdf', 'mimeType': 'application/pdf', 'createdTime': '2023-01-01T10:00:00Z'},
                {'id': '2', 'name': 'Scan_001.pdf', 'mimeType': 'application/pdf', 'createdTime': '2023-01-02T10:00:00Z'},
                {'id': '3', 'name': 'Duplicate_Invoice.pdf', 'mimeType': 'application/pdf', 'md5Checksum': 'abc', 'createdTime': '2023-01-03T10:00:00Z'},
                {'id': '4', 'name': 'Duplicate_Invoice_Copy.pdf', 'mimeType': 'application/pdf', 'md5Checksum': 'abc', 'createdTime': '2023-01-03T10:05:00Z'}
            ]

        if not self.service:
            if not self.authenticate():
                return []

        results = self.service.files().list(
            pageSize=page_size, 
            fields="nextPageToken, files(id, name, mimeType, parents, md5Checksum, createdTime)",
            q=query
        ).execute()
        return results.get('files', [])

    def download_file(self, file_id, file_name, destination_folder):
        if self.is_mock:
            print(f"MOCK: Downloading {file_name}...")
            # Create a dummy file
            path = os.path.join(destination_folder, file_name)
            with open(path, 'w') as f:
                f.write("Mock Content")
            return path

        if not self.service:
            if not self.authenticate():
                return None
        
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(os.path.join(destination_folder, file_name), 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            # print(f"Download {int(status.progress() * 100)}%.")
        
        return os.path.join(destination_folder, file_name)

    def upload_file(self, file_path, parent_id=None, new_name=None):
        if self.is_mock:
            print(f"MOCK: Uploading {file_path} as {new_name}")
            return {'id': 'new_mock_id'}

        file_metadata = {'name': new_name or os.path.basename(file_path)}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        return file

    def create_folder(self, folder_name, parent_id=None):
        if self.is_mock:
            return 'mock_folder_id'

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
            
        file = self.service.files().create(body=file_metadata,
                                            fields='id').execute()
        return file.get('id')

    def move_file(self, file_id, current_parents, new_parent_id):
        if self.is_mock:
            print(f"MOCK: Moving {file_id} to {new_parent_id}")
            return True

        try:
            # Retrieve the existing parents to remove
            file = self.service.files().get(fileId=file_id,
                                            fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))
            
            # Move the file by adding the new parent and removing the old one
            self.service.files().update(fileId=file_id,
                                        addParents=new_parent_id,
                                        removeParents=previous_parents,
                                        fields='id, parents').execute()
            return True
        except Exception as e:
            print(f"Error moving file: {e}")
            return False

    def delete_file(self, file_id):
        if self.is_mock:
            print(f"MOCK: Deleting {file_id}")
            return True

        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
