"""
A library to help with VVWare HCX migration.
"""
import json

from migration.utils import MakeApiRequest
from migration import console, logger
from . import constants


class HCX:
    """
    Get the VM and other objects from the HCX Manager
    """

    def __init__(self, url, auth_token):
        self.url = f"https://{url}"
        self.api_url = f"https://{url}/hybridity/api"
        self.auth_token = auth_token
        self.headers = {
            "Accept": "application/json",
            "Content-Type": 'application/json',
            "x-hm-authorization": self.auth_token
        }
        self.make_api_request = MakeApiRequest(self.api_url, self.headers)

    def make_hcx_request(self, method, endpoint: str, **kwargs):
        """
        Generic wrapper around request module specifically for HCX
        :param method: str: request method - GET, POST,etc
        :param endpoint: str: hcx api endpoint
        :return: dict:
        :rtype: dict
        """
        response = self.make_api_request(method=method, endpoint=endpoint, **kwargs)
        return response

    def get_hcx_networks(self):
        """
        Function to retrieve all networks configuration
        :return: list of networks
        :rtype: list
        """
        endpoint = "service/inventory/networks"
        return self.make_hcx_request(method="Post", endpoint=endpoint, data=json.dumps(constants.ALL_FILTERS))

    def get_hcx_containers(self):
        """
        Get details of the destination resources - datacenter,folder,compute  resource pools,etc.
        :return: list of resource containers
        :rtype: list
        """
        endpoint = "service/inventory/containers"
        return self.make_hcx_request(method="Post", endpoint=endpoint, data=json.dumps(constants.ALL_FILTERS))

    def get_hcx_storage_profiles(self):
        """
        Get details storage profiles configured for the HCX manager.
        :return: list of storage profiles
        :rtype: list
        """
        endpoint = "service/inventory/storageProfiles"
        return self.make_hcx_request(method="Post", endpoint=endpoint, data=json.dumps(constants.EMPTY_FILTER))

    def get_hcx_data_stores(self):
        """
        Get details of Datastores configured for HCX manager
        :return: list of Datastore
        :rtype: list
        """
        endpoint = "service/inventory/datastores"
        return self.make_hcx_request(method="Post", endpoint=endpoint, data=json.dumps(constants.ALL_FILTERS))

    def get_hcx_vms(self):
        """
        Get details of all Virtual Machines on HCX manager
        :return: list of Virtual Machines
        :rtype: list
        """
        endpoint = "service/inventory/virtualmachines"
        return self.make_hcx_request(method="Post", endpoint=endpoint, data=json.dumps(constants.VM_FILTER))

    def get_hcx_endpoints(self):
        """
        Get details of destination and source endpoint
        :return: list of Datastore
        :rtype: list
        """
        endpoint = "service/inventory/resourcecontainer/list"
        return self.make_hcx_request(method="Post", endpoint=endpoint, data=json.dumps(constants.ALL_FILTERS))

    def migrate(self, migration_objects: list, action: str):
        """
        Function to perform migration related activities such as validation and starting migration itself
        :param action: str: one of validate,start
        :param migration_objects: payload of migration objects
        :return: list of migration ids
        """
        endpoint = f"mobility/migrations/{action}"
        payload = {
            "items": migration_objects
        }
        return self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(payload))

    def get_migration_status(self, migration_id: str):
        """
        Function to check migration status
        :param migration_id: str: migration ids returned from migrate function
        :return: dict
        """
        endpoint = f"migrations/?action=query"
        payload = {
            "filter": {
                "migrationId": [migration_id]
            },
            "options": {
                "compat": 2.1
            }
        }
        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(payload))
        return response[0]["state"]
