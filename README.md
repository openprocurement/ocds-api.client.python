# OCDS.client.python

A `python` data retrieving and synchronization client for the OCDS API.

## Installation 

Simply run from command line:
```
pip install ocds_client
```

## Usage 
### Retrieve
```py
from ocds_client.clients import RecordClient
```
```py
client = RecordClient('http//')
```
To get a single `record` by `ocid` use method `get_record`:
```py
record = client.get_record('ocid')
```
To get multiple `records` by`page id` use method `get_records`:
```py
records = client.get_records({'size': n , 'page': 'page id'})
```
Similar actions can be taken with the client for `Releases`. 
```py
from ocds_client.clients import ReleaseClient
```
Use methods `get_release` and `get_realeses`. 

### Synchronization
To synchronize, use `SyncClient` when initializing the **OCDS API host** and the resource to synchronize with.
```py
from ocds_client.sync import SyncClient
client = SyncClient('http//', 'record')
for record in client.get_resource_items ():
	# do smth with record
```
