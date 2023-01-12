import time
from os import getenv
import typer
from dotenv import load_dotenv
from migration import console
from migration.hcx import HCX
from migration import utils
from typing import List

load_dotenv()
app = typer.Typer()

hcx_username = getenv("USERNAME")
hcx_password = getenv("PASSWORD")
hcx_url = getenv("HCX_URL")

# initialize hcx
console.print("Establishing connection to HCX", style="bold green")
token = utils.authenticate(url=hcx_url, username=hcx_username, password=hcx_password)
hcx = HCX(url=hcx_url, auth_token=token)
console.print("Connection to HCX established", style="bold green")


@app.command()
def check_migration_status(migration_ids: List[str]):
    status = ""

    while status != "MIGRATION_COMPLETE":
        for migration_id in migration_ids:
            status = hcx.get_migration_status(migration_id)
            typer.echo(f"MigrationID: {migration_id}, Status: {status}")
            time.sleep(10)


@app.command()
def virtual_machine(filename: str):
    """
    Function to migrate a VM from using HCX Sentinel Agent
    :param filename: str: cvs file containing the migration configuration
    ;return: None
    """

    console.print("Starting VM  migration", style="bold green")

    # read migration config
    vm_list = utils.read_migration_config(filename=filename)

    # retrieve datacenter,storage,compute,folder etc from HCX manager
    console.print("Gathering data for datacenter, storage, compute, folder, resources, networks", style="bold green")
    endpoints = hcx.get_hcx_endpoints()
    vms = hcx.get_hcx_vms()
    data_stores = hcx.get_hcx_data_stores()
    storage_profiles = hcx.get_hcx_storage_profiles()
    networks = hcx.get_hcx_networks()
    containers = hcx.get_hcx_containers()
    print(vms)
    console.print("Found configurations for datacenter, storage, compute, folder, resources, networks",
                  style="bold green")

    migration_items = []
    bad_migration_items = []

    # iterate over the list of VMs
    for vm in vm_list:
        console.print(f"Generating migration config for {vm['vmName']}", style="bold green")
        migration_item = utils.configure_migration_item(
            vm=vm,
            endpoints=endpoints,
            vms=vms,
            storage_profiles=storage_profiles,
            data_stores=data_stores,
            containers=containers,
            networks=networks
        )
        console.print(f"Done. Config generated successfully for  {vm['vmName']}", style="bold green")
        console.print(f"Validating the configuration for  {vm['vmName']}", style="bold green")
        validation = hcx.migrate(migration_objects=[migration_item], action="validate")
        if "migrationId" in validation[0]:
            console.print(f"Done. Validation is successfully for  {vm['vmName']}", style="bold green")
            migration_items.append(migration_item)
        else:
            console.print(f"Errors found for  {vm['vmName']},{validation}", style="bold red")
            bad_migration_items.append({"vmName": vm["vmName"], "errors": validation})
    console.print_json(data=migration_items)
    if migration_items:
        console.print(f"Initiating the migration", style="bold green")
        migration = hcx.migrate(migration_objects=migration_items, action="start")
        console.print(f"Note, migrationId of this request can be found at outputs/migration_ids.csv",
                      style="bold white")
        utils.write_csv_file("migration_ids", migration)
        print(migration)


if __name__ == "__main__":
    app()
