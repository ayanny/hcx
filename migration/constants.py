from schema import Schema

# define schema to validate CSV file
migration_schema = Schema([
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
    }
])
