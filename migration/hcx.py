"""
A library to help with VVWare HCX migration.
"""
import json

from migration.utils import authenticate, MakeApiRequest
from migration import console, logger


def payload_filter(entity_type: str = None, local: bool = False, remote: bool = False, endpoint_id: str = None):
    """
    Get the payload for the filter
    :param endpoint_id:
    :param entity_type: str: type of the entity
    :param local: bool: local filter
    :param remote: bool: remote filter
    :return: dict: payload for the filter
    :rtype: dict
    """
    payload = {
        "filter": {
            "cloud": {
                "local": local,
                "remote": remote
            },
            "entityType": [entity_type],
            "endpointId": endpoint_id
        },
        "options": {
            "compat": 2.1
        }
    }
    return payload


class HCX:
    """
    Get the VM object from the HCX endpoint
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
        self.switch_over_type = "OsAssistedMigration"
        self.transfer_type = "OsAssistedReplication"
        self.migration_type = "OsAssistedMigration"
        self.make_api_request = MakeApiRequest(self.api_url, self.headers)
        self.migration_options = {
            "forcePowerOffVm": False,
            "removeISOs": True,
            "removeSnapshots": True,
            "upgradeHardware": False,
            "retainMac": False,
            "upgradeVMTools": False,
            "retainTags": True,
            "replicateSecurityTags": True,
            "updateCustomAttributes": True,
            "removeCbrc": True,
            "removeCbt": True
        }
        self.local_filter = {
            "filter": {
                "cloud": {
                    "local": True
                }
            }
        }
        self.remote_filter = {
            "filter": {
                "cloud": {
                    "remote": True
                }
            }
        }
        self.all_filter = {
            "filter": {
                "cloud": {
                    "remote": True,
                    "local": True
                }
            }
        }

    def get_destination_network(self, network_name):
        """
        Get details of the destination network.
        :param network_name: str: name of the destination network
        :return: dict: details of the destination network
        :rtype: dict
        """
        endpoint = "service/inventory/networks"
        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(self.remote_filter))
        if response:
            try:
                networks = response["data"]["items"]
                return [{
                    "destNetworkType": network["type"],
                    "destNetworkValue": network["href"],
                    "destNetworkHref": network["href"],
                    "destNetworkName": network["name"],
                    "destNetworkDisplayName": network["name"],
                    "destNetworkId": network["href"]
                } for network in networks if network["name"] == network_name][0]
            except KeyError:
                logger.error(f"Error: No configuration found for the network {network_name}")
                console.print(f"Error: No configuration found for the network {network_name}", style="bold red")
                return None
        else:
            return None

    def get_destination_resource(self, resource_name, resource_type, endpoint_id: str = None):
        """
        Get details of the destination resources - datacenter,folder,compute  resource pools,etc.
        :param endpoint_id: str: endpoint id
        :param resource_name: str: name of the destination resource
        :param resource_type: str: type of the destination resource,e.g datacenter,folder,compute  resource pools,etc.
        :return: dict: details of the destination resource
        """
        endpoint = "service/inventory/containers"
        payload = payload_filter(entity_type=resource_type, remote=True, endpoint_id=endpoint_id)
        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(payload))
        if response:
            try:
                resources = response["data"]["items"]
                if endpoint_id:
                    print(endpoint_id)
                    return [{
                        "id": resource["entity_id"],
                        "name": resource_name,
                        "type": resource["entityType"]
                    } for resource in resources if
                        resource["name"] == resource_name and resource["_origin"]["endpointId"] == endpoint_id][0]
                return [{
                    "id": resource["entity_id"],
                    "name": resource_name,
                    "type": resource["entityType"]
                } for resource in resources if resource["name"] == resource_name][0]
            except KeyError:
                logger.error(f"Error: No configuration found for the resource pool {resource_name}")
                console.print(f"Error: No configuration found for the resource pool {resource_name}", style="bold red")
                return None
        else:
            return None

    def get_storage_profile(self, storage_profile_name: str):
        """
        Get details of the destination storage profile.
        :param storage_profile_name: str: name of the destination storage profile
        :return: storage profile details
        :rtype: dict
        """
        endpoint = "service/inventory/storageProfiles"
        payload = {
            "filter": {
                "entityType": "storageProfile"
            }
        }

        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(payload))
        if response:
            try:
                storage_profiles = response["data"]["items"]
                return [{
                    "option": storage_profile["entityType"],
                    "value": storage_profile["type"],
                    "type": storage_profile["type"],
                    "name": storage_profile["name"]
                } for storage_profile in storage_profiles if storage_profile["name"] == storage_profile_name][0]
            except KeyError:
                logger.error(f"Error: No configuration found for the storage profile {storage_profile_name}")
                console.print(f"Error: No configuration found for the storage profile {storage_profile_name}",
                              style="bold red")
                return None
        else:
            return None

    def get_hcx_endpoint(self, resource_name: str, endpoint_type: str):
        """
        Function to retrieve cloud configuration endpoint
        :param endpoint_type: str: this parameter is either local or remote
        :param resource_name: str: name of the cloud resource
        :return: dict
        """
        endpoint = "service/inventory/resourcecontainer/list"

        if endpoint_type == "local":
            payload = self.local_filter
        else:
            payload = self.remote_filter
        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(payload))
        if response:
            try:
                endpoints = response["data"]["items"]

                return [{
                    "endpointId": endpoint["endpointId"],
                    "endpointName": endpoint["endpointName"],
                    "endpointType": endpoint["endpointType"],
                    "resourceId": endpoint["resourceId"],
                    "resourceType": endpoint["resourceType"],
                    "resourceName": endpoint["resourceName"],
                    "computeResourceId": endpoint["resourceId"],
                } for endpoint in endpoints if endpoint.get("resourceName") == resource_name][0]
            except KeyError:
                logger.error(f"Error: No configuration found for the endpoint {resource_name}")
                console.print(f"Error: No configuration found for the endpoint {resource_name}", style="bold red")
                return None
        else:
            return None

    def get_destination_datastore(self, datastore_name: str, disk_provision_type: str):
        """
        Get details of the destination datastore.
        :param datastore_name: str: name of the destination datastore
        :param disk_provision_type: str: disk provision type - thin or thick or eagerzeroedthick
        :return: dict: details of the destination datastore
        """
        endpoint = "service/inventory/datastores"
        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(self.remote_filter))
        if response:
            try:
                data_stores = response["data"]["items"]
                return [{
                    "id": datastore["entity_id"],
                    "name": datastore_name,
                    "type": datastore["entityType"],
                    "diskProvisionType": disk_provision_type
                } for datastore in data_stores if datastore["name"] == datastore_name][0]
            except KeyError:
                logger.error(f"Error: No configuration found for the datastore {datastore_name}")
                console.print(f"Error: No configuration found for the datastore {datastore_name}", style="bold red")
                return None
        else:
            return None

    def get_destination_storage(self, datastore_name, disk_provision_type, storage_profile_name):
        """
        Get details of the destination storage configuration
        :param datastore_name: str: name of the destination datastore
        :param disk_provision_type:
        :param storage_profile_name:
        :return:
        """
        storage_profile = self.get_storage_profile(storage_profile_name=storage_profile_name)
        storage_profile_details = {
            "storageParams": [
                storage_profile
            ]
        }
        datastore = self.get_destination_datastore(datastore_name=datastore_name,
                                                   disk_provision_type=disk_provision_type)
        storage = datastore | storage_profile_details
        return storage

    def get_vm(self, hcx_endpoint_id: str, vm_name: str):
        """
        Function to filter vm for migration
        :param hcx_endpoint_id: hcm endpoint id
        :param vm_name: str: name of the virtual machine
        :return: dict
        """
        endpoint = f"service/inventory/virtualmachines?hcspUUID={hcx_endpoint_id}"
        payload = {
            "filter": {
                "cloud": {
                    "endpointId": hcx_endpoint_id,
                },
            },
            "paging": {
                "skipCount": 0,
                "pageSize": 1000
            }
        }
        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(payload))
        if response:
            try:
                vms = response["data"]["items"]
                return [{
                    "entityId": vm["entity_id"],
                    "entityName": vm["name"],
                    "entityType": vm["entityType"],
                    "summary": vm["summary"]
                } for vm in vms if vm["name"] == vm_name][0]
            except KeyError:
                logger.error(f"Error: No configuration found for the virtual machine {vm_name}")
                console.print(f"Error: No configuration found for the virtual machine {vm_name}", style="bold red")
                return None
        else:
            return None

    def get_source_network(self, hcx_endpoint_id: str, vm_name: str):
        """
        Function to filter vm for migration
        :param hcx_endpoint_id: hcm endpoint id
        :param vm_name: str: name of the virtual machine
        :return: dict
        """
        endpoint = f"service/inventory/virtualmachines?hcspUUID={hcx_endpoint_id}"
        payload = {
            "filter": {
                "cloud": {
                    "endpointId": hcx_endpoint_id,
                    # "resourceId": hcx_resource_id
                },
            },
            "paging": {
                "skipCount": 0,
                "pageSize": 1000
            }
        }
        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(payload))
        if response:
            try:
                vms = response["data"]["items"]
                return [{
                    "srcNetworkType": vm["network"][0]["type"],
                    "srcNetworkValue": vm["network"][0]["value"],
                    "srcNetworkHref": vm["network"][0]["id"],
                    "srcNetworkName": vm["network"][0]["name"],
                    "srcNetworkDisplayName": vm["network"][0]["displayName"],
                    "srcNetworkId": vm["network"][0]["id"],
                    "deviceInfo": vm["networkDevices"][0]
                } for vm in vms if vm["name"] == vm_name][0]
            except KeyError:
                logger.error(f"Error: No configuration found for the virtual machine {vm_name}")
                console.print(f"Error: No configuration found for the virtual machine {vm_name}", style="bold red")
                return None
        else:
            return None

    def get_migration_inputs(self,
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
            "migrationType": self.migration_type,
            "entity": vm,
            "source": source_endpoint,
            "destination": destination_endpoint,
            "transferParams": {
                "transferType": self.transfer_type,
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
                "switchoverType": self.switch_over_type,
                "schedule": schedule,
                "options": self.migration_options,
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

    def set_vm_placement(self, folder_name: str,
                         resource_pool_name: str,
                         datacenter_name: str,
                         destination_endpoint_id: str):
        """
        Function to set the vm placement
        :param folder_name:
        :param resource_pool_name:
        :param datacenter_name:
        :param destination_endpoint_id:
        :return:
        """
        folder = self.get_destination_resource(resource_name=folder_name, resource_type="folder")
        resource_pool = self.get_destination_resource(resource_name=resource_pool_name, resource_type="resourcePool")
        datacenter = self.get_destination_resource(resource_name=datacenter_name, resource_type="datacenter",
                                                   endpoint_id=destination_endpoint_id)
        return [folder, resource_pool, datacenter]

    def get_network_mappings(self, hcx_endpoint_id: str, vm_name: str, network_name: str):
        """
        Function to get the network mappings
        :param hcx_endpoint_id:
        :param vm_name:
        :param network_name:
        :return:
        """

        source_network = self.get_source_network(hcx_endpoint_id=hcx_endpoint_id, vm_name=vm_name)
        destination_network = self.get_destination_network(network_name=network_name)
        network_map = source_network | destination_network | {"bindingType": "static"}
        return [network_map]

    def migrate(self, migration_objects: list, action: str):
        """
        Function to validate the migration input
        :param action:
        :param migration_objects:
        :return:
        """
        endpoint = f"mobility/migrations/{action}"
        payload = {
            "items": migration_objects
        }
        response = self.make_api_request(method="POST", endpoint=endpoint, data=json.dumps(payload))
        if response:
            try:
                migrations = response["items"]
                return [{"migrationId": migration["migrationId"]} for migration in migrations]
            except KeyError:
                logger.error(f"Error: No  migrationId found for {migration_objects}")
                console.print(f"Error: No  migrationId found for {migration_objects}",
                              style="bold red")
                return None
        else:
            return None

    def get_migration_status(self, migration_id: str):
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

        if response:
            try:
                return response["data"]["items"][0]["state"]
            except KeyError:
                logger.error(f"Error: No  status found for {migration_id}")
                console.print(f"Error: No  status found for {migration_id}",
                              style="bold red")
                return None
        else:
            return None
