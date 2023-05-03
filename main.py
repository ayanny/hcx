import json
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


def get_hcx_instance(username, password, url):
    token = utils.authenticate(url=url, username=username, password=password)
    return HCX(url=hcx_url, auth_token=token)


@app.command(no_args_is_help=True)
def check_status(
        id: List[str] = typer.Option(
            ...,
            "--id",
            help="List of migration IDs",
            prompt_required=True
        )
):
    """
    Function to check the status of a migration
    :param id: List[str]: list of migration IDs
    :return: None
    """
    console.print("Establishing connection to HCX", style="bold green")

    hcx = get_hcx_instance(hcx_username, hcx_password, hcx_url)

    console.print("Connection to HCX established", style="bold green")

    status = ""
    completed_migrations = []
    while status != "MIGRATION_COMPLETE":
        for migration_id in id:
            if migration_id in completed_migrations:
                continue
            progress = hcx.get_migration_status(migration_id)
            logs = progress[0]["progress"]["log"]
            status = progress[0]["state"]
            if status == "MIGRATION_COMPLETE":
                completed_migrations.append(migration_id)
            log_messages = [log['message'] for log in logs]
            console.print(f"[green]MigrationID:[/green] {migration_id}, "
                          f"[magenta]Status:[/magenta] {status}, "
                          f"[blue]LogMessages:[/blue] "
                          f"{log_messages}"
                          )
        time.sleep(5)


@app.command(no_args_is_help=True)
def migrate_vm(
        filename: str = typer.Option(
            ..., "--filename", "-f",
            help="CSV file containing the migration config",
            prompt_required=True
        )
):
    """
    Function to migrate a VM  using HCX Sentinel Agent
    :param filename: str: cvs file containing the migration configuration
    ;return: None
    """

    migration_items = []
    bad_migration_items = []

    console.print("Starting VM  migration", style="bold green")

    # read migration config
    vm_list = utils.read_migration_config(filename=filename)

    console.print("Establishing connection to HCX", style="bold green")

    hcx = get_hcx_instance(hcx_username, hcx_password, hcx_url)
    console.print("Connection to HCX established", style="bold green")

    console.print("Gathering data for endpoints", style="bold green")
    endpoints = hcx.get_endpoints()
    console.print("Found configurations for endpoints", style="bold green")

    console.print("Taking inventory of Virtual Machines in the source Datacenter", style="bold green")
    vms = hcx.get_vms()
    console.print("Inventory retrieved successfully", style="bold green")

    console.print("Gathering Data stores details in the  Datacenter", style="bold green")
    data_stores = hcx.get_data_stores()
    console.print("Found configurations for data stores", style="bold green")

    console.print("Gathering Storage Profiles details in the destination Datacenter", style="bold green")
    storage_profiles = hcx.get_storage_profiles()
    console.print("Found configurations for storage profiles", style="bold green")

    console.print("Gathering Network details in the destination Datacenter", style="bold green")
    networks = hcx.get_networks()
    console.print("Found configurations for networks", style="bold green")

    console.print("Gathering info for containers", style="bold green")
    containers = hcx.get_containers()
    console.print("Found configurations for containers", style="bold green")

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
        console.print(json.dumps(migration_item, indent=4))

        console.print(f"Validating the configuration for  {vm['vmName']}", style="bold green")
        validation = hcx.migrate(migration_objects=[migration_item], action="validate")
        console.print(f"Done. Validation completed for {vm['vmName']}", style="bold green")

        try:
            errors = validation["items"][0].get("errors")
            if errors:
                console.print(f"Errors found for {vm['vmName']}: {errors}", style="bold red")
                bad_migration_items.append({"vmName": vm["vmName"], "errors": errors})
        except TypeError:
            if validation[0].get("migrationId"):
                console.print(f"Done. Validation is successful for {vm['vmName']}", style="bold green")
                migration_items.append(migration_item)

    if migration_items:
        console.print(f"Initiating migration task", style="bold green")
        migration = hcx.migrate(migration_objects=migration_items, action="start")
        console.print(f"Note, migrationId of this request can be found at outputs/migration_ids.csv",
                      style="bold white")
        utils.write_csv_file("migration_ids", migration)

        console.print(json.dumps(migration, indent=4))

        console.print(f"Migration task scheduled successfully", style="bold green")


if __name__ == "__main__":
    app()
