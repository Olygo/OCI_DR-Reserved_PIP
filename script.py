#!/usr/bin/python3.6

# coding: utf-8

# - - - - - - - - - - - - - - - - - - - - - - - - - - - -
#
# Author: Florian Bonneville
# Version: 1.0 - November 21th, 2023
#
# Disclaimer: 
# This script is an independent tool developed by 
# Florian Bonneville and is not affiliated with or 
# supported by Oracle. It is provided as-is and without 
# any warranty or official endorsement from Oracle
#

import oci
import argparse
import requests
import json

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# retrieve command line argument
# - - - - - - - - - - - - - - - - - - - - - - - - - -

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-pip', default='', dest='pip_id', required=True,
                        help='Reserved Public Ip Ocid')
    return parser.parse_args()

arg = parse_arguments()

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# extract instance ocid from instance metadata
# - - - - - - - - - - - - - - - - - - - - - - - - - -

headers = {'Authorization': 'Bearer Oracle'}
url = 'http://169.254.169.254/opc/v2/instance'
response = requests.get(url, headers=headers)

if response.status_code == 200:
    metadata = json.loads(response.text)
    compute_ocid = metadata['id']
    print(f"Compute_instance_ocid:\n{compute_ocid}\n")
else:
   print("Unable to retrieve instance metadata:", response, "\n")
   raise SystemExit(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# OCI authentication (Instance Principals)
# - - - - - - - - - - - - - - - - - - - - - - - - - -

signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
config = {'region': signer.region, 'tenancy': signer.tenancy_id}
identity_client=oci.identity.IdentityClient(config=config, signer=signer)

virtual_network_client = oci.core.VirtualNetworkClient(config=config, signer=signer)
compute_client = oci.core.ComputeClient(config=config, signer=signer)

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# retrieve instance vnic & private ip id
# - - - - - - - - - - - - - - - - - - - - - - - - - -

instance=compute_client.get_instance(compute_ocid).data
print("Compute_instance_data:\n", instance, "\n")

vnic_attachments=compute_client.list_vnic_attachments(
    compartment_id=instance.compartment_id, 
    instance_id=compute_ocid).data
print("Vnic_attachements:\n", vnic_attachments, "\n")

vnic_id=vnic_attachments[0].vnic_id
print("Vnic_id:\n", vnic_id, "\n")

private_ip = virtual_network_client.list_private_ips(vnic_id=vnic_id).data[0]
print("Private_ip_id:\n", private_ip.id, "\n")
print("Private_ip_data:\n", private_ip, "\n")

# - - - - - - - - - - - - - - - - - - - - - - - - - -
# search for the reserved PIP in AD
# - - - - - - - - - - - - - - - - - - - - - - - - - -

list_public_ips_response = oci.pagination.list_call_get_all_results(
    virtual_network_client.list_public_ips,
    scope="AVAILABILITY_DOMAIN",
    compartment_id=instance.compartment_id,
    availability_domain=instance.availability_domain,
    lifetime="EPHEMERAL").data

for ip in list_public_ips_response:

    if ip.private_ip_id == private_ip.id:
        ephemeral_public_ip_id = ip.id
        print("Ephemeral_public_ip:\n", ip, "\n")

        # remove ephemeral public_ip
        virtual_network_client.delete_public_ip(
            public_ip_id=ephemeral_public_ip_id)
        
        # update public IP to link it to the private IP
        virtual_network_client.update_public_ip(
            arg.pip_id,
            oci.core.models.UpdatePublicIpDetails(
                private_ip_id=private_ip.id))

        updated_public_ip_response = oci.wait_until(
            virtual_network_client,
            virtual_network_client.get_public_ip(arg.pip_id),
            evaluate_response=lambda r: r.data.lifecycle_state in ['AVAILABLE', 'ASSIGNED'])

        print(f'Updated_public_ip_response:\n{updated_public_ip_response.data}\n')
        print("*** SCRIPT COMPLETED***")
