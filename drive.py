import logging
import googleapiclient.discovery
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
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
            except Exception as e:
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
        about_info = SERVICE.about().get(fields="user").execute()
        logging.info(f"Authenticated as: {about_info['user']['displayName']}")  # Display the authenticated user's name
        if VERBOSE:
            print("Logged in to Google Drive API successfully.")
            print(f"Authenticated as: {about_info['user']['displayName']}")  # Display the authenticated user's name
        return SERVICE
    except Exception as e:
        logging.error(f"Error accessing Google Drive: {e}")
        print(f"Error accessing Google Drive: {e}")
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

def file_id_from_link(link: str) -> str | None:
    """
    Supported formats include:
    - https://drive.google.com/file/d/<id>/view
    - https://drive.google.com/file/d/<id>/preview
    - https://drive.google.com/open?id=<id>
    - https://drive.google.com/uc?id=<id>
    - https://drive.google.com/drive/folders/<id>
    - URLs containing /u/0/, /u/1/, etc.
    """
    patterns = [
        r"drive\.google\.com(?:/u/\d+)?/file/d/([a-zA-Z0-9_-]+)",       # /file/d/<id>
        r"drive\.google\.com(?:/u/\d+)?/open\?id=([a-zA-Z0-9_-]+)",     # /open?id=<id>
        r"drive\.google\.com(?:/u/\d+)?/uc\?id=([a-zA-Z0-9_-]+)",       # /uc?id=<id>
        r"drive\.google\.com(?:/u/\d+)?/drive/folders/([a-zA-Z0-9_-]+)" # /drive/folders/<id>
    ]
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    return None


def file_exists(service:googleapiclient.discovery.Resource, filename:str, folder_id:str)->bool:
    #todo
    pass

def drive_link_works(video_link:str)->bool:
    response = requests.get(video_link)
    if response.status_code // 100 == 2:
        return True
    else:
        return False

def folder_exists(service:googleapiclient.discovery.Resource, folder_id:str)->bool:
    try:
        # Attempt to get the folder metadata
        folder = service.files().get(fileId=folder_id, fields='id').execute()
        return True  # Folder exists
    except Exception as e:
        # If the folder does not exist, an error will be raised
        logging.error(f"Folder id:{folder_id} doesn't exist . error - {e}")
        return False  # Folder does not exist

def set_folder_id(service, folder_id:str):
    global UPLOADING_FOLDER_ID
    if folder_exists(service, folder_id):
        UPLOADING_FOLDER_ID = folder_id


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
    if VERBOSE: print(f"Uploading '{file_name}' ...")
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
        shareable_link = f"https://drive.google.com/file/d/{file_id}/preview"
        logging.info(f"File uploaded successfully: {shareable_link}")
        if VERBOSE: print(f"File uploaded successfully: {shareable_link}")
        return shareable_link

    except Exception as e:
        print(f"Error uploading video: {e}")
        logging.error(f"Error uploading video: {e}")
        return None

def remove_file(service:googleapiclient.discovery.Resource, file_id:str)->bool:
    try:
        service.files().delete(fileId=file_id).execute()
        if VERBOSE: print(f"File {file_id} deleted successfully.")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def mass_remove_files_from_links(service:googleapiclient.discovery.Resource, files_links:list)->list:
    ids_list = [file_id_from_link(link) for link in files_links]
    valid_ids_list = [file_id for file_id in ids_list if file_id]
    return mass_remove_files(service=service, ids_list=valid_ids_list)

def mass_remove_files(service:googleapiclient.discovery.Resource, ids_list:list)->list:
    VERBOSE = False
    fails = 0
    fail_ids = []
    for i in range(len(ids_list)):
        if remove_file(service, ids_list[i]):
            print(f"{i},,{ids_list[i]}")
        else:
            fails += 1
            fail_ids.append(ids_list[i])
    if fails:
        print("Number of failed Google Drive file removals:"+str(fails))
        print(f"Couldn't remove the Drive videos with these ids: {fail_ids}")
    return fail_ids


def authenticate_and_upload(auth_function, filepath:str, folder_id:str, upload_name:str)->str|None:
    # Main function to upload a video and return the shareable link.
    service = auth_function()
    if service:
        return upload_public_video(service, filepath, folder_id, upload_name)
    return None

def init():
    authenticate_oauth() # SERVICE auth google account & Mass Screenloom app
    prompt_uploading_folder_link() # UPLOADING_FOLDER_ID

def test()->None:
    video_filepath = "output/test_many_2.mp4"  # Local path to the video
    upload_name = "Test load pickle.mp4"  # Name of the file when uploaded
    init()
    #link = authenticate_and_upload(authenticate_oauth, video_filepath, UPLOADING_FOLDER_ID, upload_name)

def main():
    #test()
    authenticate_oauth()

# Example usage
if __name__ == "__main__":
    print("drive in main")
    main()