import csv
import json
import requests
from . import logger, console
from .constants import migration_schema
from schema import SchemaError

# disable insure login
requests.packages.urllib3.disable_warnings()


def read_migration_config(filename: str) -> list:
    """
    Read a CSV file and return a list of dictionaries.
    :param filename: str:  base filename of the CSV file
    :return: list of dictionaries
    :rtype: list
    """
    if not filename:
        raise ValueError("You must specify migration file of type csv.")
    console.print(f"Reading Migration Configuration from  {filename}", style="bold green")

    try:
        with open(filename, "r") as f:
            try:
                migration_config = list(csv.DictReader(f))
                migration_schema.validate(migration_config)
                console.print("Found valid configuration file", style="bold green")
                return migration_config
            except SchemaError as e:
                logger.error(e)
                console.print(f"Error: {e}", style="bold red")
                return []
    except FileNotFoundError:
        logger.error(f"File {filename} not found.")


def authenticate(url: str, username: str, password: str):
    """
    Authenticate to HCX and return a token.
    :param url: str: HCX URL
    :param username: str: HCX username
    :param password: str: HCX password
    :return: authorization token
    """

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {"username": username, "password": password}

    if url.split(":")[0] == "https":
        url = url
    else:
        url = "https://" + url
    try:
        endpoint = url + "/hybridity/api/sessions"
        response = requests.post(url=endpoint, headers=headers, data=json.dumps(payload), verify=False)
        token = response.headers["x-hm-authorization"]
        return token
    except requests.exceptions.RequestException as e:
        logger.error(e)
        console.print_exception(extra_lines=8, show_locals=True)
        return None


class MakeApiRequest:
    def __init__(self, base_url, headers):
        self.url = base_url
        self.headers = headers

    def __call__(self, method: str, endpoint: str, **kwargs):
        try:
            url = "{}/{}".format(self.url, endpoint)
            response = requests.request(method=method,url=url, headers=self.headers, verify=False, **kwargs)

            if response.status_code in [200, 201, 202] and response.json():
                return response.json()
        except requests.exceptions.RequestException as e:
            console.print_exception(extra_lines=8, show_locals=True)
            logger.error(e)
