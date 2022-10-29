import argparse
import json
from collections import Counter

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]
OWNERS = []


def get_drive_service():
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)
    service = build("drive", "v3", credentials=creds)
    return service


def process_all_files(service, folder_id):
    next_page_token = None
    while True:
        try:
            print(".", end="")
            items = service.files().list(q=f"'{folder_id}' in parents and not trashed",
                                         fields="files(id, mimeType, owners), nextPageToken",
                                         pageToken=next_page_token).execute()
            for item in items["files"]:
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    process_all_files(service, item["id"])
                else:
                    global OWNERS
                    OWNERS.append(item["owners"][0]["emailAddress"])
            next_page_token = items.get("nextPageToken")
            if not next_page_token:
                break

        except HttpError as e:
            print(f"\nAn error occurred: {e}")
            break


def main():
    msg = "This script counts the number of files owned by different users in a given Google Drive folder and all its subfolders."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-f", "--folder",
                        help="ID of the Google Drive folder. The user's root directory will be used if left empty.",
                        default="root")
    args = parser.parse_args()
    service = get_drive_service()
    print("Counting", end="")
    process_all_files(service, args.folder)
    print(" [✓]")
    print(json.dumps(dict(Counter(OWNERS)), sort_keys=True, indent=4))


if __name__ == "__main__":
    main()
