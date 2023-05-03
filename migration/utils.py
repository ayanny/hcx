import csv
import json
import requests
from schema import SchemaError
from pathlib import Path
from . import constants
from . import logger, console
from typing import Dict, List

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
        raise ValueError("You must specify migration file of type csv")
    console.print(
        f"Reading Migration Configuration from  {filename}", style="bold green"
    )

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
        response = requests.post(
            url=endpoint, headers=headers, data=json.dumps(payload), verify=False
        )
        token = response.headers["x-hm-authorization"]
        return token
    except requests.exceptions.RequestException as e:
        logger.error(e)
        console.print_exception(extra_lines=8, show_locals=True)
        return None


def get_endpoint(data: list, resource_name: str, is_local_endpoint: bool) -> dict:
    """
    Get the endpoint information from the migration config
    :param data: list: list of dictionaries
    :param resource_name: str: name of the resource
    :param is_local_endpoint: bool: is the endpoint local
    :return: dict: endpoint information
    """
    return [
        {
            "endpointId": endpoint["endpointId"],
            "endpointName": endpoint["endpointName"],
            "endpointType": endpoint["endpointType"],
            "resourceId": endpoint["resourceId"],
            "resourceType": endpoint["resourceType"],
            "resourceName": endpoint["resourceName"],
            "computeResourceId": endpoint["resourceId"],
        }
        for endpoint in data
        if endpoint.get("resourceName") == resource_name
        and endpoint.get("isLocal") == is_local_endpoint
    ][0]


def get_vm_info(data: list, vm_name: str):
    """
    Get the VM information from the migration config
    :param data: list: list of dictionaries
    :param vm_name: str: name of the VM
    :return: dict: VM information
    """
    return [
        {
            "entityId": vm["entity_id"],
            "entityName": vm["name"],
            "entityType": vm["entityType"],
            "summary": vm["summary"],
        }
        for vm in data
        if vm["name"] == vm_name
    ][0]


def get_vm_network_info(data: list, vm_name: str):
    """
    Get the VM network information from the migration config
    :param data: list: list of dictionaries
    :param vm_name: str: name of the VM
    :return: dict: VM network information
    """
    return [
        {
            "srcNetworkType": vm["network"][0]["type"],
            "srcNetworkValue": vm["network"][0]["value"],
            "srcNetworkHref": vm["network"][0]["id"],
            "srcNetworkName": vm["network"][0]["name"],
            "srcNetworkDisplayName": vm["network"][0]["displayName"],
            "srcNetworkId": vm["network"][0]["id"],
            "deviceInfo": vm["networkDevices"][0],
        }
        for vm in data
        if vm["name"] == vm_name
    ][0]


def get_data_store_info(data: list, data_store_name: str, disk_provision_type: str):
    """
    Get the datastore information from the migration config
    :param data: list: list of dictionaries
    :param data_store_name: str: name of the datastore
    :param disk_provision_type: str: disk provision type
    :return: dict: datastore information
    """
    return [
        {
            "id": datastore["entity_id"],
            "name": data_store_name,
            "type": datastore["entityType"],
            "diskProvisionType": disk_provision_type,
        }
        for datastore in data
        if datastore["name"] == data_store_name
    ][0]


def get_storage_profile_info(data: list, storage_profile_name: str):
    """
    Get the storage profile information from the migration config
    :param data: list: list of dictionaries
    :param storage_profile_name: str: name of the storage profile
    :return: dict: storage profile information
    """
    return [
        {
            "option": storage_profile["entityType"],
            "value": storage_profile["type"],
            "type": storage_profile["type"],
            "name": storage_profile["name"],
        }
        for storage_profile in data
        if storage_profile["name"] == storage_profile_name
    ][0]


def get_destination_network_info(data: list, network_name: str):
    """
    Get the destination network information from the migration config
    :param data: list: list of dictionaries
    :param network_name: str: name of the destination network
    :return: dict: destination network information
    """
    for network in data:
        if network["name"] == network_name:
            return {
                "destNetworkType": network["type"],
                "destNetworkValue": network["href"],
                "destNetworkHref": network["href"],
                "destNetworkName": network["name"],
                "destNetworkDisplayName": network["name"],
                "destNetworkId": network["href"],
            }
    return None


def get_resource_info(data: list, resource_name: str, endpoint_id: str = None):
    """
    Get the resource information from the migration config
    :param data: list: list of dictionaries
    :param resource_name: str: name of the resource
    :param endpoint_id: str: endpoint id
    :return: dict: resource information
    """
    matching_resources = [
        {
            "id": resource["entity_id"],
            "name": resource_name,
            "type": resource["entityType"],
        }
        for resource in data
        if resource["name"] == resource_name
        and (not endpoint_id or resource["_origin"]["endpointId"] == endpoint_id)
    ]
    if matching_resources:
        return matching_resources[0]
    return None


def write_csv_file(filename: str, rows: list):
    """
    Function to write a CSV file
    :param filename: str: name of the file
    :param rows: list: list of dictionaries
    :return: None
    """
    file_path = Path("migration_outputs") / f"{filename}.csv"
    file_path.parent.mkdir(exist_ok=True)
    headers = ["migrationId", "migrationGroupId", "entityId"]
    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(rows)


def generate_migration_payload(
    source_endpoint: Dict,
    destination_endpoint: Dict,
    networks: List[Dict],
    vm: Dict,
    vm_placement: List[Dict],
    destination_datastore: Dict,
    storage_profile: Dict,
    schedule: Dict = None,
    guest_customization: Dict = None,
) -> Dict:
    """
    Function to generate a migration payload
    :param source_endpoint: dictionary containing the source endpoint information
    :param destination_endpoint: dictionary containing the destination endpoint information
    :param networks: list of dictionaries containing the network mappings
    :param vm: dictionary containing the VM information
    :param vm_placement: list of dictionaries containing the VM placement information
    :param destination_datastore: dictionary containing the destination datastore information
    :param storage_profile: dictionary containing the storage profile information
    :param schedule: dictionary containing the schedule information (optional)
    :param guest_customization: dictionary containing the guest customization information (optional)
    :return: dictionary containing the migration payload
    """
    if schedule is None:
        schedule = {}

    storage = destination_datastore | {"storageParams": [storage_profile]}
    # storage_params = [storage_profile]
    # storage = {
    #     "datastore": destination_datastore,
    #     "storageParams": storage_params,
    # }

    transfer_profile = [
        {"option": "removeSnapshots", "value": True},
        {"option": "removeISOs", "value": True},
        {"option": "longRecovery", "value": False},
    ]
    transfer_params = {
        "transferType": constants.TRANSFER_TYPE,
        "schedule": schedule,
        "continuousSync": False,
        "longRecovery": True,
        "transferProfile": transfer_profile,
    }

    switchover_params = {
        "switchoverType": constants.SWITCH_OVER_TYPE,
        "schedule": schedule,
        "options": constants.MIGRATION_OPTIONS,
        "switchoverProfile": [],
    }
    guest_os_customization = {
        "networkCustomizations": [guest_customization],
    }
    network_params = {"networkMappings": networks}

    return {
        "migrationType": constants.MIGRATION_TYPE,
        "entity": vm,
        "source": source_endpoint,
        "destination": destination_endpoint,
        "transferParams": transfer_params,
        "switchoverParams": switchover_params,
        "placement": vm_placement,
        "storage": {"defaultStorage": storage},
        "networkParams": network_params,
        "guestCustomization": guest_os_customization,
    }


def configure_vm_placement(
    data,
    folder_name: str,
    resource_pool_name: str,
    datacenter_name: str,
    endpoint_id: str,
):
    """
    Function to configure the VM placement
    :param data: list of dictionaries containing the migration config
    :param folder_name: str: name of the folder
    :param resource_pool_name: str: name of the resource pool
    :param datacenter_name: str: name of the datacenter
    :param endpoint_id: str: endpoint id
    :return: list of dictionaries containing the VM placement information
    """
    folder = get_resource_info(data=data, resource_name=folder_name)
    resource_pool = get_resource_info(data=data, resource_name=resource_pool_name)
    datacenter = get_resource_info(
        data=data, resource_name=datacenter_name, endpoint_id=endpoint_id
    )
    return [folder, resource_pool, datacenter]


def configure_network_mapping(source_network, destination_network):
    """
    Function to configure the network mapping
    :param source_network: dictionary containing the source network information
    :param destination_network: dictionary containing the destination network information
    :return: list of dictionaries containing the network mapping information
    """
    return [source_network | destination_network | {"bindingType": "static"}]


def configure_guest_customization(vm: dict):
    """
    Function to configure the guest customization
    :param vm: dictionary containing the VM information
    :return: dictionary containing the guest customization information
    """
    valid_keys = ["macAddress", "ipAddress", "netmask", "gateways", "dns", "dnsSuffix"]
    result_dict = {}
    for key, value in vm.items():
        if key in valid_keys:
            result_dict[key] = value
    return result_dict


def configure_storage_mapping(storage_profile, datastore):
    """
    Function to configure the storage mapping
    :param storage_profile: dictionary containing the storage profile information
    :param datastore: dictionary containing the datastore information
    :return: dictionary containing the storage mapping information
    """
    storage_profile_details = {"storageParams": [storage_profile]}
    storage = datastore | storage_profile_details
    return storage


def configure_migration_item(
    vm: dict,
    endpoints: list,
    vms: list,
    data_stores: list,
    storage_profiles: list,
    containers: list,
    networks: list,
):
    """
    Function to configure the migration item
    :param vm: dictionary containing the VM information
    :param endpoints: list of dictionaries containing the endpoint information
    :param vms: list of dictionaries containing the VM information
    :param data_stores: list of dictionaries containing the datastore information
    :param storage_profiles: list of dictionaries containing the storage profile information
    :param containers: list of dictionaries containing the container information
    :param networks: list of dictionaries containing the network information
    :return: dictionary containing the migration item information
    """
    source_endpoint = get_endpoint(
        data=endpoints, is_local_endpoint=True, resource_name=vm["sourceEndpoint"]
    )

    destination_endpoint = get_endpoint(
        data=endpoints, is_local_endpoint=False, resource_name=vm["destinationEndpoint"]
    )
    destination_endpoint_id = destination_endpoint["endpointId"]

    vm_info = get_vm_info(vms, vm_name=vm["vmName"])

    vm_network_info = get_vm_network_info(data=vms, vm_name=vm["vmName"])

    data_store_info = get_data_store_info(
        data=data_stores,
        data_store_name=vm["destinationDataStore"],
        disk_provision_type=vm["diskProvisionType"],
    )

    storage_profile_info = get_storage_profile_info(
        data=storage_profiles, storage_profile_name=vm["storageProfileName"]
    )

    vm_placement_info = configure_vm_placement(
        data=containers,
        datacenter_name=vm["destinationDatacenter"],
        folder_name=vm["destinationFolder"],
        resource_pool_name=vm["destinationResourcePool"],
        endpoint_id=destination_endpoint_id,
    )
    destination_network_info = get_destination_network_info(
        data=networks, network_name=vm["destinationNetwork"]
    )

    network_mappings = configure_network_mapping(
        source_network=vm_network_info, destination_network=destination_network_info
    )

    guest_customization_info = configure_guest_customization(vm=vm)

    migration_payload = generate_migration_payload(
        source_endpoint=source_endpoint,
        destination_endpoint=destination_endpoint,
        networks=network_mappings,
        vm=vm_info,
        vm_placement=vm_placement_info,
        destination_datastore=data_store_info,
        storage_profile=storage_profile_info,
        guest_customization=guest_customization_info,
    )

    return migration_payload


class MakeApiRequest:
    """
    Class to make API requests
    """
    def __init__(self, base_url, headers):
        self.url = base_url
        self.headers = headers

    def __call__(self, method: str, endpoint: str, **kwargs):
        url = f"{self.url}/{endpoint}"
        try:
            response = requests.request(
                method=method, url=url, headers=self.headers, verify=False, **kwargs
            )
            response_json = response.json()
            status_code = response.status_code
            if 200 <= status_code < 300:
                if "data" in response_json and "items" in response_json["data"]:
                    return response_json["data"]["items"]
                elif "items" in response_json:
                    return response_json["items"]
                else:
                    return response_json
            else:
                return response_json
        except requests.exceptions.RequestException as e:
            console.print_exception(extra_lines=8, show_locals=True)
            logger.error(e)
            return None
