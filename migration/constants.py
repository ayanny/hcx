from schema import Schema, Optional


SWITCH_OVER_TYPE = "OsAssistedMigration"
TRANSFER_TYPE = "OsAssistedReplication"
MIGRATION_TYPE = "OsAssistedMigration"
# define schema to validate CSV file
MIGRATION_SCHEMA = Schema(
    [
        {
            "vmName": str,
            "sourceEndpoint": str,
            "destinationEndpoint": str,
            "destinationDataStore": str,
            "diskProvisionType": str,
            "destinationResourcePool": str,
            "destinationFolder": str,
            "destinationNetwork": str,
            "destinationDatacenter": str,
            "storageProfileName": str,
            "migrationProfile": str,
            "ipAddress": Optional(str),
            "macAddress": Optional(str),
            "netmask": Optional(str),
            "gateways": Optional(str),
            "dns": Optional(str),
            "dnsSuffix": Optional(str),
        }
    ]
)

MIGRATION_OPTIONS = {
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
    "removeCbt": True,
}

ALL_FILTERS = {"filter": {"cloud": {"remote": True, "local": True}}}
EMPTY_FILTER = {"filter": {}}
VM_FILTER = {
    "filter": {
        "cloud": {"remote": True, "local": True},
    },
    "paging": {"skipCount": 0, "pageSize": 1000},
}

LOCAL_FILTER = {"filter": {"cloud": {"local": True}}}
REMOTE_FILTER = {"filter": {"cloud": {"remote": True}}}
