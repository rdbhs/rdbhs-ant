# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "google-api-python-client>=2.198.0",
#     "google-auth>=2.55.2",
#     "google-auth-oauthlib>=1.4.0",
#     "python-dotenv>=1.2.2",
# ]
# ///

import io
import logging
import os
import pickle
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)


SCOPES = ["https://www.googleapis.com/auth/drive"]

ANT_EXECUTION_ID = os.environ.get("ANT_EXECUTION_ID")
if ANT_EXECUTION_ID:
    LANDING_PATH = Path(os.environ.get("ANT_LANDING_PATH"))

else:
    load_dotenv(Path(__file__).parent.parent / ".env")
    LANDING_PATH = Path(os.environ.get("LANDING_PATH"))

SECRET_FILES_PATH = Path(os.environ.get("SECRET_FILES_PATH"))
FILES = [
    "appointments.csv",
    "leads.csv",
    "services.csv",
    "diagnosis.csv",
    "contacts.csv",
]


def get_token():
    token = None
    token_path = SECRET_FILES_PATH / "token.pkl"
    if os.path.exists(token_path):
        with open(token_path, "rb") as token_file:
            token = pickle.load(token_file)

    if not token or not token.valid:
        if token and token.expired and token.refresh_token:
            token.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                SECRET_FILES_PATH / "google_credentials.json", SCOPES
            )
            token = flow.run_local_server(port=0)
        with open(token_path, "wb") as token_file:
            pickle.dump(token, token_file)

    return token


def download_file(file_name: str):
    token = get_token()
    service = build("drive", "v3", credentials=token)
    file_found = False

    query = f"name contains '{file_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get("files", [])

    if not items:
        logger.warning("File not found")
    else:
        file_found = True
        for file in items:
            file_id = file["id"]
            file_name = file["name"]

            request = service.files().get_media(fileId=file_id)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_base_name, file_extension = os.path.splitext(file_name)
            download_path = LANDING_PATH / f"alleva_{file_base_name}"
            download_path.mkdir(parents=True, exist_ok=True)
            destination_file = (
                download_path / f"{file_base_name}_{timestamp}{file_extension}"
            )
            with io.FileIO(destination_file, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                logger.info(f"Downloading '{file_name}'")
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        logger.info(f"Progress: {int(status.progress() * 100)}%")

            service.files().delete(fileId=file_id).execute()
            logger.info(f"File deleted from Google Drive")

    return file_found


def download_alleva_data():
    for file in FILES:
        download_file(file)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    download_alleva_data()
