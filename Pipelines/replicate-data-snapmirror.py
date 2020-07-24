# Kubeflow Pipeline Definition: Replicate data - SnapMirror

import kfp.dsl as dsl
import kfp.components as comp
from kubernetes import client as k8s_client


# Define function that triggers the creation of a NetApp snapshot
def netappSnapMirrorUpdate(
    ontapClusterMgmtHostname: str, 
    sourceSvm: str,
    sourceVolume: str,
    destinationSvm: str,
    destinationVolume: str,
    verifySSLCert: str = 'no'
) -> int :
    # Install ansible package
    import sys, subprocess
    print("Installing required Python modules:\n")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'ansible', 'netapp-lib'])
    
    # Retrieve ONTAP cluster admin account details from mounted K8s secrets
    usernameSecret = open('/mnt/secret/username', 'r')
    ontapClusterAdminUsername = usernameSecret.read().strip()
    passwordSecret = open('/mnt/secret/password', 'r')
    ontapClusterAdminPassword = passwordSecret.read().strip()
    
    # Define Ansible playbook for triggering SnapMirror update
    snapMirrorPlaybookContent = """
---
- name: "Trigger SnapMirror Update"
  hosts: localhost
  tasks:
  - name: update snapmirror
    na_ontap_snapmirror:
      state: present
      source_path: '%s:%s'
      destination_path: '%s:%s'
      hostname: '%s'
      username: '%s'
      password: '%s'
      https: 'yes'
      validate_certs: '%s'""" % (sourceSvm, sourceVolume, destinationSvm, destinationVolume, ontapClusterMgmtHostname, 
        ontapClusterAdminUsername, ontapClusterAdminPassword, verifySSLCert)
    print("\nCreating Ansible playbook.\n")
    snapMirrorPlaybookFile = open("/root/snapmirror-update.yaml", "w")
    snapMirrorPlaybookFile.write(snapMirrorPlaybookContent)
    snapMirrorPlaybookFile.close()

    # Trigger SnapMirror update
    print("Executing Ansible playbook to trigger SnapMirror update:\n")
    try :
        subprocess.run(['ansible-playbook', '/root/snapmirror-update.yaml'])
    except Exception as e :
        print(str(e).strip())
        raise

    # Return success code
    return 0

# Convert netappSnapMirrorUpdate function to Kubeflow Pipeline ContainerOp named 'NetappSnapMirrorUpdateOp'
NetappSnapMirrorUpdateOp = comp.func_to_container_op(netappSnapMirrorUpdate, base_image='python:3')


# Define Kubeflow Pipeline
@dsl.pipeline(
    name="Replicate Data - SnapMirror",
    description="Template for triggering a NetApp SnapMirror update in order to replicate data across environments"
)
def replicate_data_snapmirror(
    # Define variables that the user can set in the pipelines UI; set default values
    destination_ontap_cluster_mgmt_hostname: str = "10.61.188.40", 
    destination_ontap_cluster_admin_acct_k8s_secret: str = "ontap-cluster-mgmt-account",
    ontap_api_verify_ssl_cert: str = "yes",
    source_svm: str = "ailab",
    source_volume: str = "sm",
    destination_svm: str = "ai221_data",
    destination_volume: str = "sm_dest"
) :
    # Pipeline Steps:

    # Trigger SnapMirror replication
    replicate = NetappSnapMirrorUpdateOp(
        destination_ontap_cluster_mgmt_hostname, 
        source_svm,
        source_volume,
        destination_svm,
        destination_volume,
        ontap_api_verify_ssl_cert
    )
    # Mount k8s secret containing ONTAP cluster admin account details
    replicate.add_pvolumes({
        '/mnt/secret': k8s_client.V1Volume(
            name='ontap-cluster-admin',
            secret=k8s_client.V1SecretVolumeSource(
                secret_name=destination_ontap_cluster_admin_acct_k8s_secret
            )
        )
    })

if __name__ == '__main__' :
    import kfp.compiler as compiler
    compiler.Compiler().compile(replicate_data_snapmirror, __file__ + '.yaml')