import json

from migration.utils import MakeApiRequest
from .constants import ALL_FILTERS, EMPTY_FILTER, VM_FILTER


class HCX:
    def __init__(self, url, auth_token):
        self.url = f"https://{url}"
        self.api_url = f"{self.url}/hybridity/api"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-hm-authorization": auth_token,
        }
        self.make_api_request = MakeApiRequest(self.api_url, self.headers)

    def make_request(self, method, endpoint, payload=None):
        response = self.make_api_request(
            method=method,
            endpoint=endpoint,
            data=json.dumps(payload) if payload else None,
        )
        return response

    def _get_data(self, endpoint, filter=ALL_FILTERS):
        return self.make_request("POST", endpoint, filter)

    def get_networks(self):
        return self._get_data("service/inventory/networks")

    def get_containers(self):
        return self._get_data("service/inventory/containers")

    def get_storage_profiles(self):
        return self._get_data("service/inventory/storageProfiles", filter=EMPTY_FILTER)

    def get_data_stores(self):
        return self._get_data("service/inventory/datastores")

    def get_vms(self, skip_count=0, page_size=1000):
        vm_filter = VM_FILTER.copy()
        vm_filter["paging"]["skipCount"] = skip_count
        vm_filter["paging"]["pageSize"] = page_size
        return self._get_data("service/inventory/virtualmachines", filter=vm_filter)

    def get_endpoints(self):
        return self._get_data("service/inventory/resourcecontainer/list")

    def migrate(self, migration_objects, action):
        endpoint = f"mobility/migrations/{action}"
        payload = {"items": migration_objects}
        return self.make_request("POST", endpoint, payload)

    def get_migration_status(self, migration_id):
        endpoint = "migrations/?action=query"
        payload = {
            "filter": {"migrationId": [migration_id]},
            "options": {"compat": 2.1},
        }
        return self.make_request("POST", endpoint, payload)
