# kubeflow_jupyter_pipeline
This repository contains example Kubeflow pipeline definitions and Jupyter Notebooks that show how NetApp data management functions can be performed using Kubeflow and Jupyter. For comprehensive documentation on NetApp's Kubeflow and Jupyter integrations, refer to [TR-4798](https://www.netapp.com/us/media/tr-4798.pdf).

## Kubeflow Pipeline Definitions

> Note: All example Kubeflow pipeline definitions are in the 'Pipelines' folder.

### ai-training-run.py
- **Description:** Python script that creates a Kubeflow pipeline definition for an AI/ML model training run with built-in, near-instantaneous, dataset and model versioning and traceability. This is intended to demonstrate how a data scientist could define an automated AI/ML workflow that incorporates automated dataset and model versioning and traceability.
- **Instructions for Use:** When you execute this script, it will produce a Kubeflow pipeline definition in the form of a YAML file that can then be uploaded to the Kubeflow dashboard. Whenever you then execute the pipeline from the Kubeflow dashboard or via a pre-scheduled run, a snapshot of the volume that contains the dataset and a snapshot of the volume that contains the model will be triggered for versioning and traceability purposes. For detailed documentation, refer to section 7.4 in [TR-4798](https://www.netapp.com/us/media/tr-4798.pdf).
- **Dependencies:** The following Python modules are required in order to execute the script (these can be installed with pip) - kfp, Kubernetes, sys, subprocess, netapp_ontap, datetime, json
- **Compatibility:** This example pipeline only supports volumes that reside on NetApp ONTAP storage systems or software-defined instances.

### create-data-scientist-workspace.py
- **Description:** Python script that creates a Kubeflow pipeline definition for a workflow that can be used to near-instantaneously clone potentially massive datasets for use in a developer workspace. This is intended to demonstrate how a data scientist or data engineer could define an automated AI/ML workflow that incorporates the rapid cloning of datasets for use in workspaces, etc.
- **Instructions for Use:** When you execute this script, it will produce a Kubeflow pipeline definition in the form of a YAML file that can then be uploaded to the Kubeflow dashboard. Whenever you then execute the pipeline from the Kubeflow dashboard or via a pre-scheduled run, a clone of the volume that contains the dataset will be created and instructions for subsequently provisioning a Jupyter Notebook workspace with access to the new clone will be printed to the logs. For detailed documentation, refer to section 7.5 in [TR-4798](https://www.netapp.com/us/media/tr-4798.pdf).
- **Dependencies:** The following Python modules are required in order to execute the script (these can be installed with pip) - kfp, kubernetes, sys, subprocess, netapp_ontap, datetime, json
- **Compatibility:** This example pipeline is not compatible with NetApp FlexGroup volumes. At the time of this posting, FlexGroup volumes must be cloned by using ONTAP System Manager, the ONTAP CLI, or the ONTAP API, and then imported into the Kubernetes cluster. For details about importing a volume using Trident, see section 8.1 in [TR-4798](https://www.netapp.com/us/media/tr-4798.pdf).

### replicate-data-snapmirror.py
- **Description:** Python script that creates a Kubeflow pipeline definition for a workflow that can be used to trigger an asynchronous SnapMirror replication update. This is intended to demonstrate how a data scientist or data engineer could define an automated AI/ML workflow that incorporates SnapMirror replication for data movement across sites.
- **Instructions for Use:** When you execute this script, it will produce a Kubeflow pipeline definition in the form of a YAML file that can then be uploaded to the Kubeflow dashboard. Whenever you then execute the pipeline from the Kubeflow dashboard or via a pre-scheduled run, a SnapMirror replication update will be triggered via Ansible. For detailed documentation, refer to section 7.6 in [TR-4798](https://www.netapp.com/us/media/tr-4798.pdf).
- **Dependencies:** The following Python modules are required in order to execute the script (these can be installed with pip) - kfp, kubernetes, sys, subprocess, ansible, netapp-lib
- **Compatibility:** This example pipeline only supports volumes that reside on NetApp ONTAP storage systems or software-defined instances.

## Jupyter Notebooks

> Note: All example Jupyter Notebooks are in the 'Notebooks' folder.

### SnapMirror.ipynb
- **Description:** Jupyter Notebook containing Python code that can be used to trigger an asynchronous SnapMirror replication update via Ansible. This is intended to demonstrate how a data scientist could trigger a SnapMirror replication update within the interactive Jupyter Notebook environment, without having to access another, potentially unfamiliar, tool.
- **Instructions for Use:** Simply upload to a workspace that supports Jupyter Notebooks.
- **Dependencies:** The following Python modules are required in order to execute the code contained within the Notebook (these can be installed with pip) - sys, subprocess, ansible, netapp-lib
- **Compatibility:** This example notebook only supports volumes that reside on NetApp ONTAP storage systems or software-defined instances.

### Snapshot.ipynb
- **Description:** Jupyter Notebook containing Python code that can be used to trigger a snapshot for near instantaneous dataset or model versioning and/or traceability. This is intended to demonstrate how a data scientist could implement dataset or model versioning and/or traceability via snapshots from within the interactive Jupyter Notebook environment, without having to access another, potentially unfamiliar, tool.
- **Instructions for Use:** Simply upload to a workspace that supports Jupyter Notebooks. For detailed documentation, refer to section 7.2 in [TR-4798](https://www.netapp.com/us/media/tr-4798.pdf). You may also want to review [this blog post](https://netapp.io/2020/04/03/ai-ml-dl-dataset-in-jupyter/).
- **Dependencies:** The following Python modules are required in order to execute the code contained within the Notebook (these can be installed with pip) - netapp_ontap, datetime, json
- **Compatibility:** This example notebook only supports volumes that reside on NetApp ONTAP storage systems or software-defined instances.

## Disclaimers

c) 2019 NetApp Inc. (NetApp), All Rights Reserved

NetApp disclaims all warranties, excepting NetApp shall provide support of unmodified software pursuant to a valid, separate, purchased support agreement. No distribution or modification of this software is permitted by NetApp, except under separate written agreement, which may be withheld at NetApp's sole discretion.

THIS SOFTWARE IS PROVIDED BY NETAPP "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL NETAPP BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
