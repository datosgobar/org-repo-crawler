from __future__ import print_function
import httplib2
import os
from github import Github
from config import config
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None


GITHUB_CONFIG = config["github"]
SHEETS_CONFIG = config["sheets"]
SHEETS_SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
SHEETS_CLIENT_FILE = SHEETS_CONFIG["path_to_json"]
SHEETS_APPLICATION_NAME = 'crawlercron'


def get_sheets_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-crawlercron.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(
            SHEETS_CLIENT_FILE, SHEETS_SCOPES)
        flow.user_agent = SHEETS_APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    # Configurar acceso a Github
    g = Github(login_or_token=GITHUB_CONFIG[
               "token"], per_page=GITHUB_CONFIG["per_page"])
    org = g.get_organization(GITHUB_CONFIG["org_name"])
    repos = org.get_repos()

    # Configurar acceso a Google Sheets
    credentials = get_sheets_credentials()
    http = credentials.authorize(httplib2.Http())
    discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                     'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discovery_url)

    spreadsheet_id = '1wdz76jwRjzrcGAleBQur_Zgg__rf4dbJdK7OBEVPN9Q'
    range_name = 'Github!A2:R100'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        # Crear lista con los repos que ya están en la spreadsheet
        repos_names = []
        for row in values:
            repos_names.append(row[0])

    # Iterar por los resultados de github
    # Agregar a la spreadsheet en caso de que no exista

    print("-------------------------------------------")
    # Para cada repo, actualizar/escribir en la planilla
    for repo in repos:
        print(repo.name)

if __name__ == "__main__":
    main()
