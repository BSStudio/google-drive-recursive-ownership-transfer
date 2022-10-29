import argparse

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]
BATCH = None
BATCH_SIZE = 0
MAXIMUM_BATCH_SIZE = 100  # https://developers.google.com/drive/api/guides/performance#overview


def get_drive_service():
    flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
    creds = flow.run_local_server(port=0)
    service = build("drive", "v3", credentials=creds)
    return service


def callback(request_id, response, exception):
    if exception:
        print(f"\n{exception}")
    else:
        print("[✓]", end="")


def create_batch(service):
    global BATCH
    BATCH = service.new_batch_http_request(callback=callback)
    global BATCH_SIZE
    BATCH_SIZE = 0


def batch_add(service, file_id, new_owner):
    if not BATCH:
        create_batch(service)
    BATCH.add(service.permissions().create(
        fileId=file_id,
        body={
            "type": "user",
            "role": "owner",
            "emailAddress": new_owner
        },
        transferOwnership=True,
    ))
    global BATCH_SIZE
    BATCH_SIZE += 1
    if BATCH_SIZE == MAXIMUM_BATCH_SIZE:
        print("\n\nMaximum batch size reached. Executing batch...", end=" ")
        BATCH.execute()
        print("\nBatch execution finished.")
        create_batch(service)


def process_all_files(service, new_owner, folder_id, folder_name=None):
    if not folder_name:
        folder_name = service.files().get(fileId=folder_id).execute().get("name")
    print(f"\nGathering files in folder '{folder_name}'...", end="")

    next_page_token = None
    while True:
        try:
            items = service.files().list(q=f"'{folder_id}' in parents and not trashed",
                                         fields="files(id, name, mimeType, owners), nextPageToken",
                                         pageToken=next_page_token).execute()
            for item in items["files"]:
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    process_all_files(service, new_owner, item["id"], item["name"])
                if item["owners"][0]["me"]:
                    batch_add(service, item["id"], new_owner)
            next_page_token = items.get("nextPageToken")
            if not next_page_token:
                break

        except HttpError as e:
            print(f"\nAn error occurred: {e}")
            break


def main():
    msg = "This script transfers ownership of all files and folders recursively of a given Google Drive folder."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-o", "--owner", help="E-mail address of the new owner.", required=True)
    parser.add_argument("-f", "--folder",
                        help="ID of the Google Drive folder. The user's root directory will be used if left empty.",
                        default="root")
    args = parser.parse_args()
    print(f"Changing all files to owner '{args.owner}'")
    service = get_drive_service()
    process_all_files(service, args.owner, args.folder)
    if BATCH:
        print("\n\nExecuting final batch...", end=" ")
        BATCH.execute()
        print("\nBatch execution finished.")


if __name__ == "__main__":
    main()
