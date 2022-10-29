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


def batch_add(service, file_id, destination):
    if not BATCH:
        create_batch(service)
    BATCH.add(service.files().update(
        fileId=file_id,
        fields="id, parents",
        addParents=destination,
        supportsAllDrives=True
    ))
    global BATCH_SIZE
    BATCH_SIZE += 1
    if BATCH_SIZE == MAXIMUM_BATCH_SIZE:
        print("\n\nMaximum batch size reached. Executing batch...", end=" ")
        BATCH.execute()
        print("\nBatch execution finished.")
        create_batch(service)


def get_or_create_destination_folder(service, destination_folder_id, folder_name):
    try:
        folder_name = folder_name.replace("'", "\\'")
        return service.files().list(
            q=f"'{destination_folder_id}' in parents and name = '{folder_name}'"
              f" and mimeType = 'application/vnd.google-apps.folder' and not trashed",
            fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute().get("files")[0].get(
            "id")
    except IndexError:
        return service.files().create(
            body={
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [destination_folder_id]
            },
            fields="id",
            supportsAllDrives=True
        ).execute().get("id")


def remove_empty_folders(service, folder_id_list):
    for folder_id in folder_id_list:
        items = service.files().list(
            q=f"'{folder_id}' in parents and not trashed",
            fields="files(id)").execute().get("files")
        if not len(items):
            try:
                print(f"Deleting folder '{folder_id}'...", end=" ")
                service.files().delete(fileId=folder_id).execute()
                print("[✓]")
            except HttpError as e:
                print(f"[x] An error occurred: {e}")


def process_all_files(service, destination_folder_id, folder_id, folder_name=None, destination_folder_structure=None):
    if not folder_name:
        folder_name = service.files().get(fileId=folder_id).execute().get("name")
    print(f"\nGathering files in folder '{folder_name}'...", end="")

    if not destination_folder_structure:
        destination_folder_structure = [destination_folder_id]

    processed_folder_list = []
    next_page_token = None
    while True:
        try:
            items = service.files().list(q=f"'{folder_id}' in parents and not trashed",
                                         fields="files(id, name, mimeType), nextPageToken",
                                         pageToken=next_page_token).execute()
            for item in items["files"]:
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    destination_sub_folder_id = get_or_create_destination_folder(service, destination_folder_id,
                                                                                 item["name"])
                    destination_folder_structure.append(destination_sub_folder_id)
                    processed_folder_list.extend(
                        process_all_files(service, destination_sub_folder_id, item["id"], item["name"],
                                          destination_folder_structure))
                    destination_folder_structure.pop()
                else:
                    batch_add(service, item["id"], destination_folder_id)

            next_page_token = items.get("nextPageToken")
            if not next_page_token:
                break

        except HttpError as e:
            print(f"\nAn error occurred: {e}")
            break

    processed_folder_list.append(folder_id)
    return processed_folder_list


def main():
    msg = "This script moves all files and folders recursively of a given Google Drive folder."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-d", "--destination", help="ID of the destination folder where the files should be moved to.",
                        required=True)
    parser.add_argument("-f", "--folder",
                        help="ID of the Google Drive folder. The user's root directory will be used if left empty.",
                        default="root")
    args = parser.parse_args()
    print(f"Moving all files to '{args.destination}'")
    service = get_drive_service()
    processed_folders = process_all_files(service, args.destination, args.folder)
    if BATCH:
        print("\n\nExecuting final batch...", end=" ")
        BATCH.execute()
        print("\nBatch execution finished.")
    remove_empty_folders(service, processed_folders)


if __name__ == "__main__":
    main()
