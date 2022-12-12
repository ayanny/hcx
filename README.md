# HCX Migration Automation

This work attempts to migrate VirtualMachines using HCX Sentinel Agent. It's assumed that you have HCX Manager deployed in your Source Cloud Environment and the Destination Environment. Instances can be migrated using this work provided they are correctly configured with Sentinel Agent.

### Installation

1.	Clone this repo
2.  Install the required packages
```
pip install -r requirements.txt
```
3. create .env file within the root of the repo or export the following environment variables to provide authentication and authorization to the HCX manager. Note HCX_URL can be either DNS or IP
```
export USERNAME="username"
export PASSWORD="passowrd"
export HCX_URL="hcx dns or ip"
```
4. Create CSV file to include all the Virtual Machines you desire to micrate. You can find example in sample.csv

5. Execute migrate script specifying the csv file

```
python migrate --filename sample.csv
```