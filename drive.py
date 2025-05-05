import logging
import googleapiclient.discovery
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VERBOSE = True
GOOGLE_CREDENTIALS_FILEPATH = "credentials.json"
DRIVE_TOKEN_FILEPATH = "token.pickle"
UPLOADING_FOLDER_ID = str()
SERVICE = None


READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
FULL_ACCESS_SCOPE = "https://www.googleapis.com/auth/drive"
FILE_SPECIFIC_ACCESS = "https://www.googleapis.com/auth/drive.file"
METADATA_ACCESS = "https://www.googleapis.com/auth/drive.metadata.readonly"



def authenticate_oauth()->googleapiclient.discovery.Resource|None:
    global SERVICE
    scopes = [FULL_ACCESS_SCOPE] # to check if folder exists.
    creds = None
    if VERBOSE: print("Auth...")
    # Check if the token file exists
    token_file_exists = os.path.exists(DRIVE_TOKEN_FILEPATH)
    if token_file_exists:
        with open(DRIVE_TOKEN_FILEPATH, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        creds_success = None
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                creds_success = True
            except:
                logging.error(f"Error refreshing credentials: {e}\nTrying browser authentication...")
        if not creds_success:
            # browser login
            try:
                flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILEPATH, scopes)
                creds = flow.run_local_server(port=0)  # Opens a browser for user authentication
                # Save the credentials for the next run
                with open(DRIVE_TOKEN_FILEPATH, 'wb') as token:
                    pickle.dump(creds, token)
                creds_success = True
            except Exception as e:
                print(f"Error during authentication: {e}")
                logging.error(f"Error during authentication: {e}")
                return None
    try:
        SERVICE = googleapiclient.discovery.build('drive', 'v3', credentials=creds)
        if VERBOSE: print("Logged in to Google Drive API successfully.")
        return SERVICE
    except Exception as e:
        logging.error(f"Error accessing Google Drive: {e}")
        return None

# needs organization admin permission
def authenticate_service_account()->googleapiclient.discovery.Resource|None:
    """Authenticate and create the Google Drive service."""
    try:
        creds = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILEPATH)
        SERVICE = googleapiclient.discovery.build('drive', 'v3', credentials=creds)
        return SERVICE
    except Exception as e:
        logging.error(f"Error authenticating Google Drive service: {e}")
        return None

def folder_id_from_link(link:str)->str|None:
    # Drive folders pattern
    pattern = r'^(https://)?(www\.)?drive\.google\.com/drive(/u/\d+)?/folders/([a-zA-Z0-9_-]+)(\?usp=drive_link)?$'
    match = re.match(pattern, link)
    # Return the folder ID (the 4th capturing group)
    return match.group(4) if match else None

def folder_exists(service:googleapiclient.discovery.Resource, folder_id:str)->bool:
    try:
        # Attempt to get the folder metadata
        folder = service.files().get(fileId=folder_id, fields='id').execute()
        return True  # Folder exists
    except Exception as e:
        # If the folder does not exist, an error will be raised
        logging.error(str(e))
        return False  # Folder does not exist

def prompt_uploading_folder_link(): # UPLOADING_FOLDER_ID
    global UPLOADING_FOLDER_ID
    uploading_folder_link = str()
    while True:
        uploading_folder_link = input("Enter Drive uploading folder link : ")
        UPLOADING_FOLDER_ID = folder_id_from_link(uploading_folder_link)
        if folder_exists(SERVICE, UPLOADING_FOLDER_ID):
            break
        else:
            print(f"Folder {uploading_folder_link} does not exist!")

def upload_public_video(service:googleapiclient.discovery.Resource, video_filepath:str, folder_id:str, file_name:str)->str|None:
    """Upload a video file to Google Drive and return the shareable link."""
    if VERBOSE: print(f"Uploading {file_name}")
    try:
        # Create a media file upload object
        media = MediaFileUpload(video_filepath, mimetype='video/mp4')

        # Create the file metadata
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        # Upload the file
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        file_id = file.get('id')

        # Set the file permissions to be shareable
        service.permissions().create(
            fileId=file_id,
            body={
                'role': 'reader',
                'type': 'anyone'
            }
        ).execute()

        # Create the shareable link
        shareable_link = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        logging.info(f"File uploaded successfully: {shareable_link}")
        return shareable_link

    except Exception as e:
        logging.error(f"Error uploading video: {e}")
        return None

def authenticate_and_upload(auth_function, filepath:str, folder_id:str, upload_name:str)->str|None:
    # Main function to upload a video and return the shareable link.
    service = auth_function()
    if service:
        return upload_public_video(service, filepath, folder_id, upload_name)
    return None

def test()->None:
    video_filepath = "output/test_many_2.mp4"  # Local path to the video
    upload_name = "Test load pickle.mp4"  # Name of the file when uploaded
    authenticate_oauth()
    prompt_uploading_folder_link() # output : folder id
    #link = authenticate_and_upload(authenticate_oauth, video_filepath, UPLOADING_FOLDER_ID, upload_name)

def main():
    test()

# Example usage
if __name__ == "__main__":
    print("drive in main")
    main()