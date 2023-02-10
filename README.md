# HCX OSAM Migration

This work attempts to migrate VirtualMachines using HCX Sentinel Agent. It's assumed that you have HCX Manager deployed in your Source Cloud Environment and the Destination Environment. Instances can be migrated using this work provided they are correctly configured with Sentinel Agent.

### Installation

1.	Clone this repo

2.  Install the required packages. Note, it is assumed you're working in a virtual environment.
```bash
pip install -r requirements.txt
```
3. create .env file within the root of the repo or export the following environment variables to provide authentication and authorization to the HCX manager. Note HCX_URL can be either DNS or IP
```bash
export USERNAME="username"
export PASSWORD="password"
export HCX_URL="hcx dns or ip"
```
4. Create CSV file to include all the Virtual Machines you desire to migrate. You can find example in sample.csv

5. To execute the migration script, run the command below within the root of this repo; 

```bash
python migrate.py virtual-machine sample.csv
```
6. To check migration status, you will need migrationIds, these will be stored in migration_outputs/migration_ids.cvs file. 
```bash
    python migrate.py check-migration-status <migrationid-1> <migrationid-2> <migrationid-3>
```
