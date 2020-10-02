# Kubeflow Pipeline Definition: Replicate data - NetApp Cloud Sync

import kfp.dsl as dsl
import kfp.components as comp
import kubernetes.client as k8s_client


## Function for triggering an update for a specific Cloud Sync relationship
def netappCloudSyncUpdate(relationshipId: str, printResponse: bool = False, keepCheckingUntilComplete: bool = True) :
    # Install requests module
    import sys, subprocess
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests'])

    # Import needed modules
    import requests, json, time


    ## API response error class; objects of this class will be raised when an API resposne is not as expected
    class APIResponseError(Exception) :
        '''Error that will be raised when an API response is not as expected'''
        pass


    ## Generic function for printing an API response
    def printAPIResponse(response: requests.Response) :
        print("API Response:")
        print("Status Code: ", response.status_code)
        print("Header: ", response.headers)
        if response.text :
            print("Body: ", response.text)


    ## Function for obtaining access token and account ID for calling Cloud Sync API
    def netappCloudSyncAuth(refreshToken: str) :
        ## Step 1: Obtain limited time access token using refresh token

        # Define parameters for API call
        url = "https://netapp-cloud-account.auth0.com/oauth/token"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refreshToken,
            "client_id": "Mu0V1ywgYteI6w1MbD15fKfVIUrNXGWC"
        }

        # Call API to optain access token
        response = requests.post(url = url, headers = headers, data = json.dumps(data))

        # Parse response to retrieve access token
        try :
            responseBody = json.loads(response.text)
            accessToken = responseBody["access_token"]
        except :
            errorMessage = "Error obtaining access token from Cloud Sync API"
            raise APIResponseError(errorMessage, response)

        ## Step 2: Obtain account ID

        # Define parameters for API call
        url = "https://cloudsync.netapp.com/api/accounts"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + accessToken
        }

        # Call API to obtain account ID
        response = requests.get(url = url, headers = headers)

        # Parse response to retrieve account ID
        try :
            responseBody = json.loads(response.text)
            accountId = responseBody[0]["accountId"]
        except :
            errorMessage = "Error obtaining account ID from Cloud Sync API"
            raise APIResponseError(errorMessage, response)

        # Return access token and account ID
        return accessToken, accountId


    ## Function for monitoring the progress of the latest update for a specific Cloud Sync relationship
    def netappCloudSyncMonitor(refreshToken: str, relationshipId: str, keepCheckingUntilComplete: bool = True, printProgress: bool = True, printResponses: bool = False) :
        # Step 1: Obtain access token and account ID for accessing Cloud Sync API
        try :
            accessToken, accountId = netappCloudSyncAuth(refreshToken = refreshToken)
        except APIResponseError as err:
            if printResponse :
                errorMessage = err.args[0]
                response = err.args[1]
                print(errorMessage)
                printAPIResponse(response)
            raise   

        # Step 2: Obtain status of the latest update; optionally, keep checking until the latest update has completed   

        while True :
            # Define parameters for API call
            url = "https://cloudsync.netapp.com/api/relationships-v2/%s" % (relationshipId)
            headers = {
                "Accept": "application/json",
                "x-account-id": accountId,
                "Authorization": "Bearer " + accessToken
            }   

            # Call API to obtain status of latest update
            response = requests.get(url = url, headers = headers)

            # Print API response
            if printResponses :
                printAPIResponse(response)

            # Parse response to retrieve status of latest update
            try :
                responseBody = json.loads(response.text)
                latestActivityType = responseBody["activity"]["type"]
                latestActivityStatus = responseBody["activity"]["status"]
            except :
                errorMessage = "Error status of latest update from Cloud Sync API"
                raise APIResponseError(errorMessage, response)
            
            # End execution if the latest update is complete
            if latestActivityType == "Sync" and latestActivityStatus == "DONE" :
                if printProgress :
                    print("Success: Cloud Sync update is complete.")
                break

            # Print message re: progress
            if printProgress :
                print("Cloud Sync update is not yet complete.")

            # End execution if calling program doesn't want to monitor until the latest update has completed
            if not keepCheckingUntilComplete :
                break

            # Sleep for 60 seconds before checking progress again
            print("Checking again in 60 seconds...")
            time.sleep(60)


    # Retrieve Cloud Sync refresh token from mounted k8s secret
    refreshTokenSecret = open('/mnt/secret/refreshToken', 'r')
    refreshToken = refreshTokenSecret.read().strip()
    
    # Step 1: Obtain access token and account ID for accessing Cloud Sync API
    try :
        accessToken, accountId = netappCloudSyncAuth(refreshToken = refreshToken)
    except APIResponseError as err:
        errorMessage = err.args[0]
        response = err.args[1]
        print(errorMessage)
        if printResponse :
            printAPIResponse(response)
        raise

    # Step 2: Trigger Cloud Sync update

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/relationships/%s/sync" % (relationshipId)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    # Call API to trigger update
    print("Triggering Cloud Sync update.")
    response = requests.put(url = url, headers = headers)

    # Check for API response status code of 202; if not 202, raise error
    if response.status_code != 202 :
        errorMessage = "Error calling Cloud Sync API to trigger update."
        if printResponse :
            print(errorMessage)
            printAPIResponse(response)
        raise APIResponseError(errorMessage, response)

    # Print API response
    if printResponse :
        print("Note: Status Code 202 denotes that update was successfully triggered.")
        printAPIResponse(response)
    
    print("Checking progress.")
    netappCloudSyncMonitor(refreshToken = refreshToken, relationshipId = relationshipId, keepCheckingUntilComplete = keepCheckingUntilComplete, printResponses = printResponse)


# Convert netappSnapMirrorUpdate function to Kubeflow Pipeline ContainerOp named 'NetappSnapMirrorUpdateOp'
NetappCloudSyncUpdateOp = comp.func_to_container_op(netappCloudSyncUpdate, base_image='python:3')


# Define Kubeflow Pipeline
@dsl.pipeline(
    name="Replicate Data - Cloud Sync",
    description="Template for triggering an update for a specific Cloud Sync relationship in order to replicate data across environments"
)
def replicate_data_cloud_sync(
    # Define variables that the user can set in the pipelines UI; set default values
    cloud_sync_relationship_id: str,
    cloud_sync_refresh_token_k8s_secret: str = "cloud-sync-refresh-token"
) :
    # Pipeline Steps:

    # Trigger Cloud Sync update
    replicate = NetappCloudSyncUpdateOp(
        cloud_sync_relationship_id
    )
    # Mount k8s secret containing Cloud Sync refresh token
    replicate.add_pvolumes({
        '/mnt/secret': k8s_client.V1Volume(
            name='cloud-sync-refresh-token',
            secret=k8s_client.V1SecretVolumeSource(
                secret_name=cloud_sync_refresh_token_k8s_secret
            )
        )
    })

if __name__ == '__main__' :
    import kfp.compiler as compiler
    compiler.Compiler().compile(replicate_data_cloud_sync, __file__ + '.yaml')