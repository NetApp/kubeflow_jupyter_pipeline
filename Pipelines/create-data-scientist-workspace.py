import json
import kfp
import kfp.dsl as dsl

def clone_manifest(pvc_name, storage_class, size, source_pvc, jupyter_namespace) :
    manifest = '''
{
    "apiVersion": "v1",
    "kind": "PersistentVolumeClaim",
    "metadata": {
        "name": "dataset-workspace-''' + str(pvc_name) + '''",
        "namespace": "''' + str(jupyter_namespace) + '''",
        "annotations": {
            "trident.netapp.io/cloneFromPVC": "''' + str(source_pvc) + '''"
        }
    },
    "spec": {
        "accessModes": ["ReadWriteMany"],
        "storageClassName": "''' + str(storage_class) + '''",
        "resources": {
            "requests": {
                "storage": "''' + str(size) + '''"
            }
        }
    }
}
'''
    return manifest

@dsl.pipeline(
    name="Create Data Scientist Workspace",
    description="Template for cloning dataset volume in order to create data scientist/developer workspace"
)
def create_data_scientist_workspace(
    # Define variables that the user can set in the pipelines UI; set default values
    workspace_name: str = "dev",
    dataset_volume_pvc_existing: str = "gold-dataset",
    dataset_volume_pvc_existing_size: str = "10Gi",
    storage_class: str = "ontap-flexvol",
    jupyter_namespace: str = "admin"
) :

    # Create a clone of the source dataset volume from the just-created snapshot
    dataset_clone = dsl.ResourceOp(
        name='dataset-clone-for-workspace',
        k8s_resource=json.loads(clone_manifest(workspace_name, storage_class, dataset_volume_pvc_existing_size, dataset_volume_pvc_existing, jupyter_namespace)),
        action='create'
    )

    # Print instructions for deploying an interactive workspace
    print_instructions = dsl.ContainerOp(
        name="print-instructions",
        image="ubuntu:bionic",
        command=["sh", "-c"],
        arguments=['echo "To deploy an interactive workspace, provision a new Jupyter workspace in namespace, ' + str(jupyter_namespace) + ', and mount dataset volume, dataset-workspace-' + str(workspace_name) + '."']
    )
    print_instructions.after(dataset_clone)

if __name__ == '__main__' :
    kfp.compiler.Compiler().compile(create_data_scientist_workspace, __file__ + '.yaml')
