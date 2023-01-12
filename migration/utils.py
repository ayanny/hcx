import csv
import json
import os

import requests
from schema import SchemaError
from pathlib import Path
from . import constants
from . import logger, console

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
                constants.MIGRATION_SCHEMA.validate(migration_config)
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


def get_endpoint(data: list, resource_name: str, is_local_endpoint: bool) -> dict:
    return [{
        "endpointId": endpoint["endpointId"],
        "endpointName": endpoint["endpointName"],
        "endpointType": endpoint["endpointType"],
        "resourceId": endpoint["resourceId"],
        "resourceType": endpoint["resourceType"],
        "resourceName": endpoint["resourceName"],
        "computeResourceId": endpoint["resourceId"],
    } for endpoint in data if endpoint.get("resourceName") == resource_name
                              and endpoint.get("isLocal") == is_local_endpoint][0]


def get_vm_info(data: list, vm_name: str):
    return [{
        "entityId": vm["entity_id"],
        "entityName": vm["name"],
        "entityType": vm["entityType"],
        "summary": vm["summary"]
    } for vm in data if vm["name"] == vm_name][0]


def get_vm_network_info(data: list, vm_name: str):
    return [{
        "srcNetworkType": vm["network"][0]["type"],
        "srcNetworkValue": vm["network"][0]["value"],
        "srcNetworkHref": vm["network"][0]["id"],
        "srcNetworkName": vm["network"][0]["name"],
        "srcNetworkDisplayName": vm["network"][0]["displayName"],
        "srcNetworkId": vm["network"][0]["id"],
        "deviceInfo": vm["networkDevices"][0]
    } for vm in data if vm["name"] == vm_name][0]


def get_data_store_info(data: list, data_store_name: str, disk_provision_type: str):
    return [{
        "id": datastore["entity_id"],
        "name": data_store_name,
        "type": datastore["entityType"],
        "diskProvisionType": disk_provision_type
    } for datastore in data if datastore["name"] == data_store_name][0]


def get_storage_profile_info(data: list, storage_profile_name: str):
    return [{
        "option": storage_profile["entityType"],
        "value": storage_profile["type"],
        "type": storage_profile["type"],
        "name": storage_profile["name"]
    } for storage_profile in data if storage_profile["name"] == storage_profile_name][0]


def get_destination_network_info(data: list, network_name: str):
    return [{
        "destNetworkType": network["type"],
        "destNetworkValue": network["href"],
        "destNetworkHref": network["href"],
        "destNetworkName": network["name"],
        "destNetworkDisplayName": network["name"],
        "destNetworkId": network["href"]
    } for network in data if network["name"] == network_name][0]


def get_resource_info(data: list, resource_name: str, endpoint_id: str = None):
    if endpoint_id:
        return [{
            "id": resource["entity_id"],
            "name": resource_name,
            "type": resource["entityType"]
        } for resource in data if
            resource["name"] == resource_name and resource["_origin"]["endpointId"] == endpoint_id][0]
    return [{
        "id": resource["entity_id"],
        "name": resource_name,
        "type": resource["entityType"]
    } for resource in data if resource["name"] == resource_name][0]


def write_csv_file(filename: str, rows: list):
    file_path = Path(os.path.join(os.getcwd(), f"migration_outputs/{filename}.csv"))
    file_path.parent.mkdir(exist_ok=True)
    headers = ["migrationId", "migrationGroupId", "entityId"]
    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def generate_migration_payload(
        source_endpoint: dict,
        destination_endpoint: dict,
        networks: list,
        vm: dict,
        vm_placement: list,
        destination_datastore: dict,
        storage_profile: dict,
        schedule=None,
):
    """
        Function to get the migration inputs
        :param source_endpoint:
        :param destination_endpoint:
        :param networks:
        :param vm:
        :param vm_placement:
        :param destination_datastore:
        :param storage_profile:
        :param schedule:
        :return:
        """
    if schedule is None:
        schedule = {}
    storage = destination_datastore | {"storageParams": [storage_profile]}
    return {
        "migrationType": constants.MIGRATION_TYPE,
        "entity": vm,
        "source": source_endpoint,
        "destination": destination_endpoint,
        "transferParams": {
            "transferType": constants.TRANSFER_TYPE,
            "schedule": schedule,
            "continuousSync": False,
            "longRecovery": True,
            "transferProfile": [
                {
                    "option": "removeSnapshots",
                    "value": True
                },
                {
                    "option": "removeISOs",
                    "value": True
                },
                {
                    "option": "longRecovery",
                    "value": False
                }
            ],
        },
        "switchoverParams": {
            "switchoverType": constants.SWITCH_OVER_TYPE,
            "schedule": schedule,
            "options": constants.MIGRATION_OPTIONS,
            "switchoverProfile": []
        },
        "placement": vm_placement,
        "storage": {
            "defaultStorage": storage
        },
        "networkParams": {
            "networkMappings": networks
        },
    }


def configure_vm_placement(data, folder_name: str,
                           resource_pool_name: str,
                           datacenter_name: str,
                           endpoint_id: str):
    folder = get_resource_info(data=data, resource_name=folder_name)
    resource_pool = get_resource_info(data=data, resource_name=resource_pool_name)
    datacenter = get_resource_info(data=data, resource_name=datacenter_name, endpoint_id=endpoint_id)
    return [folder, resource_pool, datacenter]


def configure_network_mapping(source_network, destination_network):
    return [source_network | destination_network | {"bindingType": "static"}]


def configure_storage_mapping(storage_profile, datastore):
    storage_profile_details = {
        "storageParams": [
            storage_profile
        ]
    }
    storage = datastore | storage_profile_details
    return storage


def configure_migration_item(vm: dict, endpoints: list, vms: list,
                             data_stores: list,
                             storage_profiles: list,
                             containers: list,
                             networks: list):
   
    source_endpoint = get_endpoint(data=endpoints, is_local_endpoint=True, resource_name=vm["sourceEndpoint"])

    destination_endpoint = get_endpoint(data=endpoints, is_local_endpoint=False,
                                        resource_name=vm["destinationEndpoint"])
    destination_endpoint_id = destination_endpoint["endpointId"]

    vm_info = get_vm_info(vms, vm_name=vm["vmName"])

    vm_network_info = get_vm_network_info(data=vms, vm_name=vm["vmName"])

    data_store_info = get_data_store_info(data=data_stores, data_store_name=vm["destinationDataStore"],
                                          disk_provision_type=vm["diskProvisionType"])

    storage_profile_info = get_storage_profile_info(data=storage_profiles,
                                                    storage_profile_name=vm["storageProfileName"])

    vm_placement_info = configure_vm_placement(data=containers, datacenter_name=vm["destinationDatacenter"],
                                               folder_name=vm["destinationFolder"],
                                               resource_pool_name=vm["destinationResourcePool"],
                                               endpoint_id=destination_endpoint_id
                                               )
    destination_network_info = get_destination_network_info(data=networks, network_name=vm["destinationNetwork"])

    network_mappings = configure_network_mapping(source_network=vm_network_info,
                                                 destination_network=destination_network_info)

    migration_payload = generate_migration_payload(source_endpoint=source_endpoint,
                                                   destination_endpoint=destination_endpoint,
                                                   networks=network_mappings,
                                                   vm=vm_info,
                                                   vm_placement=vm_placement_info,
                                                   destination_datastore=data_store_info,
                                                   storage_profile=storage_profile_info)

    return migration_payload


class MakeApiRequest:
    def __init__(self, base_url, headers):
        self.url = base_url
        self.headers = headers

    def __call__(self, method: str, endpoint: str, **kwargs):
        try:
            url = "{}/{}".format(self.url, endpoint)
            response = requests.request(method=method, url=url, headers=self.headers, verify=False, **kwargs)
            if response.status_code in [200, 201, 202] and response.json().get("data"):
                return response.json()["data"]["items"]
            elif response.status_code in [200, 201, 202] and "items" in response.json():
                return response.json().get("items")
            elif response.json()["errors"]:
                return response.json()["errors"]
            else:
                return response.json()
        except requests.exceptions.RequestException as e:
            console.print_exception(extra_lines=8, show_locals=True)
            logger.error(e)
            return None
