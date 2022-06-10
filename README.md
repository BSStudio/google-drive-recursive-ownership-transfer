# Google Drive Recursive Ownership Transfer Tool

Original idea is from [davidstrauss/google-drive-recursive-ownership](https://github.com/davidstrauss/google-drive-recursive-ownership).


### Supported Files

G Suite for Government and G Suite for Education accounts can change ownership of any file owned by the current user, including uploaded/synced files suchs as PDFs.

Other Google Accounts such as G Suite for Business or Personal Google Accounts can only transfer ownership of Google files (Docs, Sheets, Sildes, Forms, Drawings, My Maps, and folders).

NOTE: Ownership can only be transferred to members of the same G Suite or Google domain. Ex. @gmail.com can only transfer to other @gmail.com addresses.

NOTE: The Google Drive API does not allow suppressing notifications for change of ownership.

CURRENT LIMITATION: Due to e-mail sending the script can only process ~2500 files before Google rejects the requests. 

### Setup

```shell
git clone https://github.com/BSStudio/google-drive-recursive-ownership-transfer
pip install -r requirements.txt
```

### Usage

First, replace the sample `client_secrets.json` with your own [client secrets](https://github.com/googleapis/google-api-python-client/blob/master/docs/client-secrets.md). Don't forget to enable Drive API for your project.

```shell
python transfer.py [-h] -o OWNER [-f FOLDER]
```

```shell
options:
  -h, --help            show this help message and exit
  -o OWNER, --owner OWNER
                        E-mail address of the new owner.
  -f FOLDER, --folder FOLDER
                        ID of the Google Drive folder. The user's root directory will be used if left empty.
```