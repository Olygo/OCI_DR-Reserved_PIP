# OCI_DR-WITH-RESERVED-PIP

In this scenario, our objective is to automatically restaure a Compute Instance from one Availability Domain (AD) to another within the same region. 
Specifically, we are transitioning from Frankfurt AD3 to AD1.

While [Full Stack Disaster Recovery](https://docs.oracle.com/en-us/iaas/disaster-recovery/index.html) facilitates the reassignment of the same Private IP, if there is a requirement to also reallocate a Reserved Public IP, utilization of the provided script becomes essential. It is imperative that this script is present locally on each compute instance, irrespective of whether it operates on a Linux or Windows environment.

# Prerequisites

This script will update the Vnic parameters from the Compute Instance, to do so it will authenticate to OCI using [Instance Principals](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/Identity/Tasks/callingservicesfrominstances.htm).

You must create the following resources:

##### Create a Dynamic Group

- Create a Dynamic Group called OCI_Scripting and add the OCID of your instance to the group, using :

```
ANY {instance.id = 'OCID_of_your_Compute_Instance'}
```	

##### Create a Policy

- Create a compartment level policy, giving your dynamic group permission to manage all-resources in this compartment:

```
allow dynamic-group OCI_Scripting to manage all-resources in compartment YOUR_COMPARTMENT_NAME
```

##### Download script locally

```
curl https://raw.githubusercontent.com/Olygo/OCI_DR-Reserved_PIP/main/script.py -o /home/opc/script.py
```

##### Grant Admin permissions to the Compute Instance run command plugin. 
The plugin runs as the ocarun user.

From [Invoke custom scripts using the run command with OCI FSDRS](https://docs.oracle.com/en/learn/full-stack-dr-run-command/index.html#introduction) apply :

- "**Task 3. Configure and validate run command in the source VM**"

```
vi ./101-oracle-cloud-agent-run-command
```

**Allow the ocarun user to run all commands as sudo by adding the following line**

```
ocarun ALL=(ALL) NOPASSWD:ALL
```

**Validate if the syntax in the configuration file is correct.**

```
visudo -cf ./101-oracle-cloud-agent-run-command
```

**Add the configuration file to /etc/sudoers.d.**

```
sudo cp ./101-oracle-cloud-agent-run-command /etc/sudoers.d/
```

**Update permisions**

```
sudo chmod 440 /etc/sudoers.d/101-oracle-cloud-agent-run-command
```

**Restart Cloud agent manually**

```
sudo systemctl restart oracle-cloud-agent
```

**Parameters for execution:**

| Argument -| Parameter                             | Description                             |
| --------- | ------------------------------------- | --------------------------------------- |
| -pip      | ocid1.publicip.oc1.eu-frankfurt-1.xxx | add the ocid of your Reserved Public Ip |



# Step by step guide

##### Compute Instance to replicate :
I want to replicate an instance (Linux or Windows) running in Frankfurt Availability Domain #3,

![00](./.images/00.png)

##### Compute Instance volumes :
Instance has 1 block volume attached

![01](./.images/01.png)

##### Compute Instance Reserved PIP :
Instance has 1 Reserved Public IP (pip) assigned

![02](./.images/02.png)

##### Create a Volume Group :
Before creating a Disaster Recovery group you must create a volume group

This volume group will protect volumes in Availability Domain #3

CONSOLE > STORAGE > VOLUME GROUPS > CREATE VOLUME GROUP

![03](./.images/03.png)

##### Volume Group - Volumes :
Add the boot & block volumes of your instance

![04](./.images/04.png)

##### Volume Group - Replication :
Enable the replication to Frankfurt Availability Domain #1

![05](./.images/05.png)

##### Create Primary Disaster Recovery Group : 
Create your Primary DRP Group, without role and members

CONSOLE > MIGRATION & DISASTER RECOVERY > DR PROTECTION GROUPS > CREATE DR PROTECTION GROUP

![06](./.images/06.png)

##### Create Standby Disaster Recovery Group : 
Create your Standby DRP Group, without role and members

![07](./.images/07.png)

##### Compute Instance to replicate :
Add a COMPUTE member to your PRIMARY DRP Group

Select the instance to protect

Select MOVING INSTANCE because we want to reuse the same IPs

Add a VNIC MAPPING in order to specify the Private IP to assign

![08](./.images/08.png)

##### Add a VOLUME GROUP member :
Select the Volume Group created previously

![09](./.images/09.png)

##### Define DRP Groups roles :
Select ASSOCIATE from your PRIMARY DRP group
 
![10](./.images/10.png)

##### Primary and Standby group roles are assigned:

![11](./.images/11.png)

##### Create a SWITCHOVER Plan from the STANDBY DRP group :

![12](./.images/12.png)

##### Reorder Plan Groups  :
Move Terminate Instance BEFORE Launch Instance

![14](./.images/14.png)

##### Reorder Plan Groups  :
Move Terminate Instance BEFORE Launch Instance

![15](./.images/15.png)

##### Add a custom Plan Group:
This task can be added after the last Plan Group

![16](./.images/16.png)

##### Set your custom Plan Group :
SCRIPT PARAMETER :
		
	sudo /usr/bin/python3.6 /home/opc/script.py -pip ocid1.publicip.oc1.eu-frankfurt-1.amaaaaaaXXXXXXXXXXXXXXX

![17](./.images/17.png)

##### Set your custom Plan Group :

![18](./.images/18.png)

##### Set your custom Plan Group :

![19](./.images/19.png)

##### DRP groups are ready to use :

![20](./.images/20.png)

##### Execute DR PLAN from Standby DRP group :

![21](./.images/21.png)

##### Execute DR PLAN from Standby DRP group :

![22](./.images/22.png)

##### DR Plan is running :

![23](./.images/23.png)

##### Compute instance deployment :
Compute instance in AD3 is terminated

Compute instance is created in AD1 using an Ephemeral Public IP

![24](./.images/24.png)

##### DR Plan executes Local custom script from the instance :

![25](./.images/25.png)

##### You can Read/Download your script outputs :

![26](./.images/26.png)

##### Instance restaured in AD1 using the same Public/Private IPs :

![27](./.images/27.png)

##### DRP groups roles have been reversed :

![28](./.images/28.png)

##### Volume Group replication has been enabled from AD1 to AD3 :

![29](./.images/29.png)


## Questions ?
**_olygo.git@gmail.com_**


## Disclaimer
**Please test properly on test resources, before using it on production resources to prevent unwanted outages or unwanted bills.**
