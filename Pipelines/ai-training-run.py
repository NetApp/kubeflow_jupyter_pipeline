# Kubeflow Pipeline Definition: AI Training Run

import kfp.dsl as dsl
import kfp.onprem as onprem
import kfp.components as comp
from kubernetes import client as k8s_client


# Define function that triggers the creation of a NetApp snapshot
def netappSnapshot(
    ontapClusterMgmtHostname: str, 
    pvName: str, 
    verifySSLCert: bool = True
) -> str :
    # Install netapp_ontap package
    import sys, subprocess;
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'netapp_ontap'])
    
    # Import needed functions/classes
    from netapp_ontap import config as netappConfig
    from netapp_ontap.host_connection import HostConnection as NetAppHostConnection
    from netapp_ontap.resources import Volume, Snapshot
    from datetime import datetime
    import json

    # Retrieve ONTAP cluster admin account details from mounted K8s secrets
    usernameSecret = open('/mnt/secret/username', 'r')
    ontapClusterAdminUsername = usernameSecret.read().strip()
    passwordSecret = open('/mnt/secret/password', 'r')
    ontapClusterAdminPassword = passwordSecret.read().strip()
    
    # Configure connection to ONTAP cluster/instance
    netappConfig.CONNECTION = NetAppHostConnection(
        host = ontapClusterMgmtHostname,
        username = ontapClusterAdminUsername,
        password = ontapClusterAdminPassword,
        verify = verifySSLCert
    )
    
    # Convert pv name to ONTAP volume name
    # The following will not work if you specified a custom storagePrefix when creating your
    #   Trident backend. If you specified a custom storagePrefix, you will need to update this
    #   code to match your prefix.
    volumeName = 'trident_%s' % pvName.replace("-", "_")
    print('\npv name: ', pvName)
    print('ONTAP volume name: ', volumeName)

    # Create snapshot; print API response
    volume = Volume.find(name = volumeName)
    timestamp = datetime.today().strftime("%Y%m%d_%H%M%S")
    snapshot = Snapshot.from_dict({
        'name': 'kfp_%s' % timestamp,
        'comment': 'Snapshot created by a Kubeflow pipeline',
        'volume': volume.to_dict()
    })
    response = snapshot.post()
    print("\nAPI Response:")
    print(response.http_response.text)

    # Retrieve snapshot details
    snapshot.get()

    # Convert snapshot details to JSON string and print
    snapshotDetails = snapshot.to_dict()
    print("\nSnapshot Details:")
    print(json.dumps(snapshotDetails, indent=2))

    # Return name of newly created snapshot
    return snapshotDetails['name']

# Convert netappSnapshot function to Kubeflow Pipeline ContainerOp named 'NetappSnapshotOp'
NetappSnapshotOp = comp.func_to_container_op(netappSnapshot, base_image='python:3')


# Define Kubeflow Pipeline
@dsl.pipeline(
    # Define pipeline metadata
    name="AI Training Run",
    description="Template for executing an AI training run with built-in training dataset traceability and trained model versioning"
)
def ai_training_run(
    # Define variables that the user can set in the pipelines UI; set default values
    ontap_cluster_mgmt_hostname: str = "10.61.188.40", 
    ontap_cluster_admin_acct_k8s_secret: str = "ontap-cluster-mgmt-account",
    ontap_api_verify_ssl_cert: bool = True,
    dataset_volume_pvc_existing: str = "dataset-vol",
    dataset_volume_pv_existing: str = "pvc-43b12235-f32e-4dc4-a7b8-88e90d935a12",
    trained_model_volume_pvc_existing: str = "kfp-model-vol",
    trained_model_volume_pv_existing: str = "pvc-236e893b-63b4-40d3-963b-e709b9b2816b",
    execute_data_prep_step__yes_or_no: str = "yes",
    data_prep_step_container_image: str = "ubuntu:bionic",
    data_prep_step_command: str = "<insert command here>",
    data_prep_step_dataset_volume_mountpoint: str = "/mnt/dataset",
    train_step_container_image: str = "nvcr.io/nvidia/tensorflow:19.12-tf1-py3",
    train_step_command: str = "<insert command here>",
    train_step_dataset_volume_mountpoint: str = "/mnt/dataset",
    train_step_model_volume_mountpoint: str = "/mnt/model",
    validation_step_container_image: str = "nvcr.io/nvidia/tensorflow:19.12-tf1-py3",
    validation_step_command: str = "<insert command here>",
    validation_step_dataset_volume_mountpoint: str = "/mnt/dataset",
    validation_step_model_volume_mountpoint: str = "/mnt/model"
) :
    # Set GPU limits; Due to SDK limitations, this must be hardcoded
    train_step_num_gpu = 0
    validation_step_num_gpu = 0

    # Pipeline Steps:

    # Execute data prep step
    with dsl.Condition(execute_data_prep_step__yes_or_no == "yes") :
        data_prep = dsl.ContainerOp(
            name="data-prep",
            image=data_prep_step_container_image,
            command=["sh", "-c"],
            arguments=[data_prep_step_command]
        )
        # Mount dataset volume/pvc
        data_prep.apply(
            onprem.mount_pvc(dataset_volume_pvc_existing, 'dataset', data_prep_step_dataset_volume_mountpoint)
        )

    # Create a snapshot of the dataset volume/pvc for traceability
    dataset_snapshot = NetappSnapshotOp(
        ontap_cluster_mgmt_hostname, 
        dataset_volume_pv_existing,
        ontap_api_verify_ssl_cert
    )
    # Mount k8s secret containing ONTAP cluster admin account details
    dataset_snapshot.add_pvolumes({
        '/mnt/secret': k8s_client.V1Volume(
            name='ontap-cluster-admin',
            secret=k8s_client.V1SecretVolumeSource(
                secret_name=ontap_cluster_admin_acct_k8s_secret
            )
        )
    })
    # State that snapshot should be created after the data prep job completes
    dataset_snapshot.after(data_prep)

    # Execute training step
    train = dsl.ContainerOp(
        name="train-model",
        image=train_step_container_image,
        command=["sh", "-c"],
        arguments=[train_step_command]
    )
    # Mount dataset volume/pvc
    train.apply(
        onprem.mount_pvc(dataset_volume_pvc_existing, 'datavol', train_step_dataset_volume_mountpoint)
    )
    # Mount model volume/pvc
    train.apply(
        onprem.mount_pvc(trained_model_volume_pvc_existing, 'modelvol', train_step_model_volume_mountpoint)
    )
    # Request that GPUs be allocated to training job pod
    if train_step_num_gpu > 0 :
        train.set_gpu_limit(train_step_num_gpu, 'nvidia')
    # State that training job should be executed after dataset volume snapshot is taken
    train.after(dataset_snapshot)

    # Create a snapshot of the model volume/pvc for model versioning
    model_snapshot = NetappSnapshotOp(
        ontap_cluster_mgmt_hostname, 
        trained_model_volume_pv_existing,
        ontap_api_verify_ssl_cert
    )
    # Mount k8s secret containing ONTAP cluster admin account details
    model_snapshot.add_pvolumes({
        '/mnt/secret': k8s_client.V1Volume(
            name='ontap-cluster-admin',
            secret=k8s_client.V1SecretVolumeSource(
                secret_name=ontap_cluster_admin_acct_k8s_secret
            )
        )
    })
    # State that snapshot should be created after the training job completes
    model_snapshot.after(train)

    # Execute inference validation job
    inference_validation = dsl.ContainerOp(
        name="validate-model",
        image=validation_step_container_image,
        command=["sh", "-c"],
        arguments=[validation_step_command]
    )
    # Mount dataset volume/pvc
    inference_validation.apply(
        onprem.mount_pvc(dataset_volume_pvc_existing, 'datavol', validation_step_dataset_volume_mountpoint)
    )
    # Mount model volume/pvc
    inference_validation.apply(
        onprem.mount_pvc(trained_model_volume_pvc_existing, 'modelvol', validation_step_model_volume_mountpoint)
    )
    # Request that GPUs be allocated to pod
    if validation_step_num_gpu > 0 :
        inference_validation.set_gpu_limit(validation_step_num_gpu, 'nvidia')
    # State that inference validation job should be executed after model volume snapshot is taken
    inference_validation.after(model_snapshot)

if __name__ == "__main__" :
    import kfp.compiler as compiler
    compiler.Compiler().compile(ai_training_run, __file__ + ".yaml")