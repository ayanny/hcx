import sys
from os import getenv

import typer
from dotenv import load_dotenv

from migration import console
from migration.hcx import HCX
from migration.utils import read_migration_config, authenticate

load_dotenv()
app = typer.Typer()

hcx_username = getenv("USERNAME")
hcx_password = getenv("PASSWORD")
hcx_url = getenv("HCX_URL")


@app.command()
def migrate_vm(filename: str = typer.Option(default="", help="Filename of the migration configuration file")):
    """
    Function to migrate a VM from using HCX Sentinel Agent
    :param filename: str: cvs file containing the migration configuration
    ;return: None
    """
    console.print("Starting migration of VMs", style="bold green")
    # initialize hcx
    try:
        console.print("Establishing connection to HCX", style="bold green")
        token = authenticate(url=hcx_url, username=hcx_username, password=hcx_password)
        hcx = HCX(url=hcx_url, auth_token=token)
        console.print("Connection to HCX established", style="bold green")
    except Exception as e:
        console.print(f"Failed to establish connection to HCX: {e}", style="bold red")
        return sys.exit(1)

    # container for migration objects
    migration_objects = []

    # read migration config
    vm_list = read_migration_config(filename=filename)
    # iterate over the list of VMs

    for vm in vm_list:
        try:

            # get the source endpoint
            source_endpoint = hcx.get_hcx_endpoint(endpoint_type="local", resource_name=vm["sourceEndpoint"])
            source_endpoint_id = source_endpoint["endpointId"]
            console.print(f"Source endpoint found: {source_endpoint['endpointName']}", style="bold green")

            destination_endpoint = hcx.get_hcx_endpoint(endpoint_type="remote", resource_name=vm["destinationEndpoint"])
            destination_endpoint_id = destination_endpoint["endpointId"]
            console.print(f"Destination endpoint found: {destination_endpoint['endpointName']}", style="bold green")

            # get the vm
            console.print(f"Searching for VM: {vm['vmName']}", style="bold green")
            vm_info = hcx.get_vm(hcx_endpoint_id=source_endpoint_id, vm_name=vm["vmName"])
            console.print(f"VM found: {vm_info['entityName']}", style="bold green")
            console.print_json(data=vm_info)

            console.print(f"Getting Network info for  VM {vm['vmName']}", style="bold green")
            networks = hcx.get_network_mappings(hcx_endpoint_id=source_endpoint_id,
                                                vm_name=vm["vmName"],
                                                network_name=vm["destinationNetwork"]
                                                )
            console.print(f"Network info for VM {vm['vmName']} found", style="bold green")
            console.print_json(data=networks)

            # get destination storage profile
            console.print(f"Getting datastore info for  VM {vm['vmName']}", style="bold green")
            destination_datastore = hcx.get_destination_datastore(
                datastore_name=vm["destinationDataStore"],
                disk_provision_type=vm["diskProvisionType"]
            )
            console.print(f"Datastore info for VM {vm['vmName']} found", style="bold green")
            console.print_json(data=destination_datastore)

            # get destination storage profile
            console.print(f"Getting storage profile info for  VM {vm['vmName']}", style="bold green")
            storage_profile = hcx.get_storage_profile(storage_profile_name=vm["storageProfileName"])
            console.print(f"Storage profile info for VM {vm['vmName']} found", style="bold green")
            console.print_json(data=storage_profile)

            # set vm placeme
            console.print(f"Configuring datacenter placement for VM {vm['vmName']}", style="bold green")
            vm_placement = hcx.set_vm_placement(datacenter_name=vm["destinationDatacenter"],
                                                folder_name=vm["destinationFolder"],
                                                resource_pool_name=vm["destinationResourcePool"],
                                                destination_endpoint_id=destination_endpoint_id
                                                )
            console.print(f"Datacenter placement for VM {vm['vmName']} configured", style="bold green")
            console.print_json(data=vm_placement)

            # set migration payload
            console.print(f"Configuring migration payload for VM {vm['vmName']}", style="bold green")
            migration_input = hcx.get_migration_inputs(source_endpoint=source_endpoint,
                                                       destination_endpoint=destination_endpoint,
                                                       networks=networks,
                                                       vm=vm_info,
                                                       vm_placement=vm_placement,
                                                       destination_datastore=destination_datastore,
                                                       storage_profile=storage_profile,
                                                       )

            migration_objects.append(migration_input)
            console.print(f"Migration payload for VM {vm['vmName']} configured", style="bold green")

        except Exception as e:
            console.print(f"Failed to migrate VM: {e}", style="bold red")
            return sys.exit(1)

    # validate migration

    try:
        # validate migration input
        console.print("Validating migration inputs", style="bold green")
        validation = hcx.migrate(migration_objects=migration_objects, action="validate")
        console.print("Migration inputs validated", style="bold green")
        console.print_json(data=validation)

        # start migration
        console.print("Starting migration", style="bold green")
        migration = hcx.migrate(migration_objects=migration_objects, action="start")
        console.print("Migration started", style="bold green")
        console.print_json(data=migration)
    except Exception as e:
        console.print(f"Failed to validate migration inputs: {e}", style="bold red")
        return sys.exit(1)


if __name__ == "__main__":
    app()
