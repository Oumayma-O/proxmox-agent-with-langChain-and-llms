class ConfigData:
    MONGO_DB_URI = "mongodb://localhost:27017/"
    DB_NAME = "proxmox_dummy"
    COLLECTION_NAME = "proxmox_dummy_inventory"
    DOCUMENT_SCHEMA= '''
                    "_id": "String",
                    "name": "String",
                    "type": "String",
                    "provider": "String",
                    "proxmox_node": "String",
                    "proxmox_instance_url": "String",
                    "vm_cpus": "Int32",
                    "vm_memory": "Int64",
                    "vm_disk_size": "Int64",
                    "network_interfaces": "Array"
                    
                    '''
    
    SCHEMA_DESCRIPTION = '''

                    Here is the description to determine what each key represents:
                    1. _id:
                        - Description: Unique identifier for the document.
                    2. name:
                        - Description: Resource common name.
                    3. type:
                        - Description: Resource type can be "Virtual Machine" or "LXC Container".
                    4. provider:
                        - Description: Resource provider.
                    5. proxmox_node:
                        - Description: On which Proxmox node the resource was provisionned.
                    6. proxmox_instance_url:
                        - Description: The Proxmox instance URL.
                    7. vm_cpus:
                        - Description: How many CPUs the resource was provisionned with.
                    8. vm_memory:
                        - Description: How much memory the resource was provisionned with. The unit is in bytes.
                    9. vm_disk_size:
                        - Description: How much disk size the resource was provisionned with. The unit is in bytes. 
                    10. network_interfaces:
                        - Description: An Array that of embedded documents, each embedded document represents a network interface.
                        Each network interface embedded document has the following fields:
                        1. "netin": The network interface name.
                        2. "mac_address": The network interface MAC address.
                        3. "ip_address": The IP address associated with the network interface.
                        4. "type": The assignment type of the IP address either "static" or "dhcp".
                        example:
                        "network_interfaces": [
                            {{
                                "netin": "net0",
                                "mac_address": "02:00:00:95:21:16",
                                "ip_address": "51.254.8.155",
                                "type": "static"
                            }}
                        ]
                    '''     

