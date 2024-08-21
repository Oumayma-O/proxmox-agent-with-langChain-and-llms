from typing import Dict, Any
import json

_proxmox_api_docs= [
    {
        "endpoint": "/api2/json/nodes/{node}/qemu",
        "method": "get",
        "summary": "List Virtual machines (VMs) on a Node",
        "parameters": [
            {
                "name": "node",
                "in": "path",
                "required": True,
                "description": "Node ID where VMs are located",
                "schema": {
                    "type": "string"
                }
            }
        ]
    },
    {
        "endpoint": "/api2/json/nodes/{node}/qemu",
        "method": "post",
        "summary": "Create a Virtual machine (VM) ",
        "description": "Use this endpoint to create a new virtual machine on the specified node. This endpoint is used for initial creation and can be used for the allocation of resources such as memory, cores, and storage.",
        "parameters": [
            {
                "name": "node",
                "in": "path",
                "required": True,
                "description": "Node ID where the VM will be created",
                "schema": {
                    "type": "string"
                }
            }
        ],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "vmid": {
                                "type": "integer",
                                "description": "VM ID"
                            },
                            "name": {
                                "type": "string",
                                "description": "Name of the VM"
                            },
                            "memory": {
                                "type": "integer",
                                "description": "Memory size in MB"
                            },
                            "cores": {
                                "type": "integer",
                                "description": "Number of CPU cores"
                            },
                            "ide0": {
                                "type": "string",
                                "description": "Disk size and format, e.g., \"local:32,format=qcow2\""
                            },
                            "net0": {
                                "type": "string",
                                "description": "Network configuration, e.g., \"virtio,bridge=vmbr0\""
                            },
                            "ostype": {
                                "type": "string",
                                "description": "OS type, e.g., \"l26\" for Linux"
                            }
                        },
                        "required": ["node", "vmid"]
                    }
                }
            }
        }
    },
    {
        'endpoint': '/api2/json/nodes/{node}/qemu/{vmid}',
        'method': 'delete',
        'summary': 'Delete Virtual machine (VM)',
        'description' : 'Deleting a Virtual machine from a node .',
        'parameters': [
                    {
                        'name': 'node',
                        'in': 'path',
                        'required': True,
                        'description': 'Node ID where the VM is located',
                        'schema': {
                            'type': 'string'
                        }
                    },
                    {
                        'name': 'vmid',
                        'in': 'path',
                        'required': True,
                        'description': 'ID of the VM to delete',
                        'schema': {
                            'type': 'string'
                        }
                    }
                ]
    },
    {
        "endpoint": "/api2/json/nodes/{node}/qemu/{vmid}/config",
        "method": "get",
        "summary": "Get Virtual machine/Vm Configuration (config file)",
        "parameters": [
            {
                "name": "node",
                "in": "path",
                "required": True,
                "description": "Node ID where the VM is located",
                "schema": {
                    "type": "string"
                }
            },
            {
                "name": "vmid",
                "in": "path",
                "required": True,
                "description": "ID of the VM",
                "schema": {
                    "type": "integer"
                }
            },
            {
                "name": "current",
                "in": "query",
                "required": False,
                "description": "Get current values instead of pending values",
                "schema": {
                    "type": "boolean"
                }
            }
        ]
    },
    {
        "endpoint": "/api2/json/nodes/{node}/qemu/{vmid}/config",
        "method": "post",
        "summary": "Set initial configuration options of a Virtual machine",
        "description": "Use this endpoint to set the initial configuration of a new virtual machine. This is useful when you need to define settings such as memory, cores, CPU type, and other parameters for a VM that is being created.",
        "parameters": [
            {
                "name": "node",
                "in": "path",
                "required": True,
                "description": "The cluster node name",
                "schema": {
                    "type": "string"
                }
            },
            {
                "name": "vmid",
                "in": "path",
                "required": True,
                "description": "The (unique) ID of the VM",
                "schema": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 999999999
                }
            }
        ],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "memory": {
                                "type": "integer",
                                "description": "Amount of RAM for the VM in MiB",
                                "minimum": 16
                            },
                            "cores": {
                                "type": "integer",
                                "description": "Number of cores per socket",
                                "minimum": 1
                            },
                            "cpu": {
                                "type": "string",
                                "description": "Emulated CPU type"
                            },
                            "name": {
                                "type": "string",
                                "description": "Set a name for the VM"
                            },
                            "net": {
                                "type": "string",
                                "description": "Specify network devices"
                            },
                            "ostype": {
                                "type": "string",
                                "description": "Specify guest operating system",
                                "enum": [
                                    "other", "wxp", "w2k", "w2k3", "w2k8", "wvista", "win7", "win8",
                                    "win10", "win11", "l24", "l26", "solaris", "opensolaris", "netbsd",
                                    "freebsd", "openbsd"
                                ]
                            },
                            "disk": {
                                "type": "string",
                                "description": "Specify disk size and type, e.g., 'size=10G,ssd=1'"
                            },
                            "boot": {
                                "type": "string",
                                "description": "Specify guest boot order, e.g., 'order=cdrom;ide0'"
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "endpoint": "/api2/json/nodes/{node}/qemu/{vmid}/config",
        "method": "put",
        "summary": "Update virtual machine configuration options",
        "description": "Use this endpoint to modify the configuration of an existing virtual machine. This is useful when you need to change settings such as memory, cores, network devices, and other VM parameters for an already running or stopped VM.",
        "parameters": [
            {
                "name": "node",
                "in": "path",
                "required": True,
                "description": "The cluster node name.",
                "schema": {
                    "type": "string"
                }
            },
            {
                "name": "vmid",
                "in": "path",
                "required": True,
                "description": "The (unique) ID of the VM.",
                "schema": {
                    "type": "integer",
                    "minimum": 100,
                    "maximum": 999999999
                }
            }
        ],
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "acpi": {
                                "type": "boolean",
                                "description": "Enable/disable ACPI."
                            },
                            "agent": {
                                "type": "string",
                                "description": "Enable/disable communication with the QEMU Guest Agent and its properties."
                            },
                            "balloon": {
                                "type": "integer",
                                "description": "Amount of target RAM for the VM in MiB. Using zero disables the balloon driver."
                            },
                            "bios": {
                                "type": "string",
                                "enum": ["seabios", "ovmf"],
                                "description": "Select BIOS implementation."
                            },
                            "cores": {
                                "type": "integer",
                                "description": "The number of cores per socket."
                            },
                            "memory": {
                                "type": "integer",
                                "description": "Amount of RAM for the VM in MiB."
                            },
                            "net0": {
                                "type": "string",
                                "description": "Network device configuration, e.g., 'model=e1000,bridge=vmbr0'."
                            },
                            "sockets": {
                                "type": "integer",
                                "description": "The number of CPU sockets."
                            },
                            "cpu": {
                                "type": "string",
                                "description": "Emulated CPU type. Format: [[cputype=]<string>] [,flags=<+FLAG[;-FLAG...]>] [,hidden=<1|0>] [,hv-vendor-id=<vendor-id>] [,phys-bits=<8-64|host>] [,reported-model=<enum>]"
                            },
                            "cpulimit": {
                                "type": "number",
                                "description": "Limit of CPU usage. Value '0' indicates no CPU limit."
                            },
                            "cpuunits": {
                                "type": "integer",
                                "description": "CPU weight for a VM. The larger the number, the more CPU time this VM gets. Range: 1 - 262144."
                            },
                            "ostype": {
                                "type": "string",
                                "enum": [
                                    "other", "wxp", "w2k", "w2k3", "w2k8", "wvista", "win7", "win8", "win10", "win11",
                                    "l24", "l26", "solaris"
                                ],
                                "description": "Specify guest operating system to enable specific optimizations/features."
                            }
                        }
                    }
                }
            }
        }
    },
    {
        "endpoint": "/api2/json/nodes/{node}/lxc",
        "methods": "get",
        "summary": "List LXC Containers on a Node",
        "description": "List all containers available on a node",
        "parameters": [
                    { 
                        "name": "node",
                        "in": "path",
                        "required": True,
                        "description": "Node ID where LXC containers are located",
                        "schema": {
                            "type": "string"
                        }
                    }
                ]
            
        
    },
    {
    "endpoint": "/api2/json/nodes/{node}/lxc",
    "methods": "post",
    "summary": "Create LXC Container",
    "parameters": [
                {
                    "name": "node",
                    "in": "path",
                    "required": True,
                    "description": "Node ID where the LXC container will be created",
                    "schema": {
                        "type": "string"
                    }
                }
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "vmid": {
                                    "type": "integer",
                                    "description": "Container ID"
                                },
                                "hostname": {
                                    "type": "string",
                                    "description": "Hostname of the container"
                                },
                                "memory": {
                                    "type": "integer",
                                    "description": "Memory size in MB"
                                },
                                "cores": {
                                    "type": "integer",
                                    "description": "Number of CPU cores"
                                },
                                "rootfs": {
                                    "type": "string",
                                    "description": "Root filesystem, e.g., 'local:10' for 10GB"
                                },
                                "net0": {
                                    "type": "string",
                                    "description": "Network configuration, e.g., 'bridge=vmbr0'"
                                },
                                "ostemplate": {
                                    "type": "string",
                                    "description": "OS template for the container"
                                }
                            },
                            "required": ["node", "vmid", "ostemplate"]
                        }
                    }
                }
            }
        
},
    {
            'endpoint': '/api2/json/nodes/{node}/lxc/{vmid}',
            'methods': 'delete',
            'summary': 'Delete LXC Container',
            'description' : 'Deleting a container from a node .',
            'parameters': [
                        {
                            'name': 'node',
                            'in': 'path',
                            'required': True,
                            'description': 'Node ID where the LXC container is located',
                            'schema': {
                                'type': 'string'
                            }
                        },
                        {
                            'name': 'vmid',
                            'in': 'path',
                            'required': True,
                            'description': 'ID of the LXC container to delete',
                            'schema': {
                                'type': 'string'
                            }
                        }
                    ]
    },
    {
        "endpoint": "/api2/json/nodes/{node}/lxc/{vmid}/config",
        "method": "put",
        "summary": "Set container configuration (config file)",
        "description": "Modify or set the configuration of an LXC container identified by {vmid} on the specified {node}.",
        "parameters": [
            {
                "name": "node",
                "in": "path",
                "required": True,
                "description": "The cluster node name",
                "schema": {
                    "type": "string"
                }
            },
            {
                "name": "vmid",
                "in": "path",
                "required": True,
                "description": "The (unique) ID of the VM",
                "schema": {
                    "type": "integer"
                }
            }
        ],
        "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "arch": { "type": "string", "enum": ["amd64", "i386", "arm64", "armhf", "riscv32", "riscv64"], "description": "OS architecture type" },
                        "cmode": { "type": "string", "enum": ["shell", "console", "tty"], "description": "Console mode" },
                        "console": { "type": "boolean", "description": "Attach a console device (/dev/console) to the container" },
                        "cores": { "type": "integer", "description": "The number of cores assigned to the container" },
                        "cpulimit": { "type": "number", "description": "Limit of CPU usage" },
                        "cpuunits": { "type": "integer", "description": "CPU weight for a container" },
                        "debug": { "type": "boolean", "description": "Try to be more verbose" },
                        "delete": { "type": "string", "description": "A list of settings you want to delete" },
                        "description": { "type": "string", "description": "Description for the Container" },
                        "dev[n]": { "type": "string", "description": "Device to pass through to the container" },
                        "digest": { "type": "string", "description": "Prevent changes if current configuration file has different SHA1 digest" },
                        "features": { "type": "string", "description": "Allow containers access to advanced features" },
                        "hookscript": { "type": "string", "description": "Script that will be executed during various steps in the container's lifetime" },
                        "hostname": { "type": "string", "description": "Set a host name for the container" },
                        "lock": { "type": "string", "enum": ["backup", "create", "destroyed", "disk", "fstrim", "migrate", "mounted", "rollback", "snapshot", "snapshot-delete"], "description": "Lock/unlock the container" },
                        "memory": { "type": "integer", "description": "Amount of RAM for the container in MB" },
                        "mp[n]": { "type": "string", "description": "Use volume as container mount point" },
                        "nameserver": { "type": "string", "description": "Sets DNS server IP address for a container" },
                        "net[n]": { "type": "string", "description": "Specifies network interfaces for the container" },
                        "onboot": { "type": "boolean", "description": "Specifies whether a container will be started during system bootup" },
                        "ostype": { "type": "string", "enum": ["debian", "devuan", "ubuntu", "centos", "fedora", "opensuse", "archlinux", "alpine", "gentoo", "nixos", "unmanaged"], "description": "OS type" },
                        "protection": { "type": "boolean", "description": "Sets the protection flag of the container" },
                        "revert": { "type": "string", "description": "Revert a pending change" },
                        "rootfs": { "type": "string", "description": "Use volume as container root" },
                        "searchdomain": { "type": "string", "description": "Sets DNS search domains for a container" },
                        "startup": { "type": "string", "description": "Startup and shutdown behavior" },
                        "swap": { "type": "integer", "description": "Amount of SWAP for the container in MB" },
                        "tags": { "type": "string", "description": "Tags of the Container" },
                        "template": { "type": "boolean", "description": "Enable/disable Template" },
                        "timezone": { "type": "string", "description": "Time zone to use in the container" },
                        "tty": { "type": "integer", "description": "Specify the number of tty available to the container" },
                        "unprivileged": { "type": "boolean", "description": "Makes the container run as unprivileged user" },
                        "unused[n]": { "type": "string", "description": "Reference to unused volumes" }
                    }
                }
            }
        }
    }
    },

   {
    "endpoint": "/api2/json/nodes/{node}/lxc/{vmid}/config",
    "method": "get",
    "summary": "Get Lxc container configuration/config ",
    "parameters": [
        {
            "name": "node",
            "in": "path",
            "required": True,
            "description": "The cluster node name",
            "schema": {
                "type": "string"
            }
        },
        {
            "name": "vmid",
            "in": "path",
            "required": True,
            "description": "The (unique) ID of the VM",
            "schema": {
                "type": "integer"
            }
        },
        {
            "name": "current",
            "in": "query",
            "required": False,
            "description": "Get current values (instead of pending values)",
            "schema": {
                "type": "boolean",
                "default": False
            }
        },
        {
            "name": "snapshot",
            "in": "query",
            "required": False,
            "description": "Fetch config values from given snapshot",
            "schema": {
                "type": "string"
            }
        }
    ]
},
{
    "endpoint": "/api2/json/access/users",
    "method": "get",
    "summary": "User index.",
    "parameters": [
        {
            "name": "enabled",
            "in": "query",
            "required": False,
            "description": "Optional filter for enable property.",
            "schema": {
                "type": "boolean",
            }
        },
        {
            "name": "full",
            "in": "query",
            "required": False,
            "description": "Include group and token information.",
            "schema": {
                "type": "boolean",
                "default": False
            }
        }
    ]
},
{
    "endpoint": "/api2/json/access/permissions",
    "method": "get",
    "summary": "Retrieve/get effective permissions of given user/token.",
    "parameters": [
        {
            "name": "path",
            "in": "query",
            "required": False,
            "description": "Only dump this specific path, not the whole tree.",
            "schema": {
                "type": "string",
            }
        },
        {
            "name": "userid",
            "in": "query",
            "required": False,
            "description": "User ID or full API token ID",
            "schema": {
                "type": "string",
            }
        }
    ]
},



    ]



proxmox_api_docs = json.dumps(_proxmox_api_docs, indent=2)