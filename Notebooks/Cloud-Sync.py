#!/usr/bin/env python
# coding: utf-8

# # Trigger Cloud Sync Replication within Jupyter Notebook

# This playbook demonstrates how to trigger a NetApp Cloud Sync update from within a Jupyter Notebook

# ## Import needed modules

# In[1]:


import requests, json, time


# ## Define classes and functions

# First, we define a class for a new error type. Errors of this type will be raised when an API resposne is not as expected

# In[2]:


## API response error class; objects of this class will be raised when an API resposne is not as expected
class APIResponseError(Exception) :
    '''Error that will be raised when an API response is not as expected'''
    pass


# Next, we define generic function for printing an API response

# In[3]:


## Generic function for printing an API response
def printAPIResponse(response: requests.Response) :
    print("API Response:")
    print("Status Code: ", response.status_code)
    print("Header: ", response.headers)
    if response.text :
        print("Body: ", response.text)


# Next, we define a function for obtaining our Cloud Sync API access token and account ID. The access token and account ID will be needed in order to call the Cloud Sync API to trigger the replication update.

# In[4]:


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


# Next, we define a function for actually triggering the Cloud Sync update

# In[5]:


## Function for triggering an update for a specific Cloud Sync relationship
def netappCloudSyncUpdate(refreshToken: str, relationshipId: str, printResponse: bool = True) :
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


# Lastly, we define a function for monitoring the progress of the latest replication update

# In[6]:


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


# ## Set Cloud Sync refresh token

# A refresh token is needed in order to obtain an access token. If you do not yet have a refresh token, you can create one here: https://services.cloud.netapp.com/refresh-token.

# In[7]:


refreshToken = "<enter your refresh token>"


# ## Optional: obtain Cloud Sync relationship ID

# If you do not already know the relationship ID for the specific Cloud Sync relationship that you wish to trigger an update for, then you must obtain it. In order to do this, we define a function for obtaining a list of all Cloud Sync relationships that are tied to our account.
# 
# If you already know the relationship id for the specific relationship that you wish to trigger an update for, then you can skip this section

# In[8]:


def netappCloudSyncGetRelationships(refreshToken: str, printResponse: bool = True) :
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

    # Step 2: Retrieve list of relationships

    # Define parameters for API call
    url = "https://cloudsync.netapp.com/api/relationships-v2"
    headers = {
        "Accept": "application/json",
        "x-account-id": accountId,
        "Authorization": "Bearer " + accessToken
    }

    # Call API to retrieve list of relationships
    response = requests.get(url = url, headers = headers)

    # Check for API response status code of 200; if not 200, raise error
    if response.status_code != 200 :
        errorMessage = "Error calling Cloud Sync API to retrieve list of relationships."
        if printResponse :
            print(errorMessage)
            printAPIResponse(response)
        raise APIResponseError(errorMessage, response)

    # Print API response
    if printResponse :
        print("API Response:")
        print("Note: Status Code 200 denotes success.")
        print("Status Code: ", response.status_code)
        print("Header: ", response.headers)
        print("Body: ", response.text)
    
    # Return json object containing response body
    responseBody = json.loads(response.text)
    return responseBody


# Now, we wil call the function that we just defined. If you receive an error, try restarting the kernel and running again.

# In[9]:


relationships = netappCloudSyncGetRelationships(refreshToken = refreshToken)


# Now, we will print out the list of relationships. Identify the specific relationship in this list that you wish to trigger an update for, and note the relationship id. You will need to enter this relationships id in the next section. If you have multiple relationship set up for the same source and destination, then you will want to change 'printFullDetails' to True.

# In[10]:


printFullDetails = False

numRelationships = 0
for relationship in relationships :
    numRelationships+=1
    print("-- Relationship #", numRelationships, "--\n")
    if printFullDetails:
        print(json.dumps(relationship, indent=2), "\n")
    else :
        print("id: ", relationship["id"])
        print("source: ", json.dumps(relationship["source"], indent=2))
        print("target: ", json.dumps(relationship["target"], indent=2), "\n")


# ## Set Cloud Sync relationship id

# Note: this is the same relationship id that we just retrieved in the previous section.

# In[11]:


relationshipId = "5ed00996ca85650009a83db2"


# ## Trigger Cloud Sync update

# Lastly, we will call the function that we defined above to trigger an update for our specified Cloud Sync relationship. If you receive an error, try restarting the kernel and running again.

# In[12]:


netappCloudSyncUpdate(refreshToken = refreshToken, relationshipId = relationshipId)


# ## Check Cloud Sync progress

# In[13]:


netappCloudSyncMonitor(refreshToken = refreshToken, relationshipId = relationshipId, keepCheckingUntilComplete = True)

