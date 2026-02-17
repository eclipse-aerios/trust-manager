import requests
import json

ngsild_cb_url = '127.0.0.1:1026'

headers = {
    'Content-Type': 'application/json',
    'aerOS': 'true'
}

payload = {
    'id': 'urn:ngsi-ld:Domain:IQB',
    'type': 'Domain',
    'description': {
        'type': 'Property',
        'value': 'IQB Domain'
    },
    'publicUrl': {
        'type': 'Property',
        'value': 'https://iqb-mvp-domain.aerios-project.eu'
    },
    'owner': {
        'type': 'Relationship',
        'object': ['urn:ngsi-ld:Organization:04']
    },
    'isEntrypoint': {
        'type': 'Property',
        'value': True
    },
    'domainStatus': {
        'type': 'Relationship',
        'object': 'urn:ngsi-ld:DomainStatus:Functional'
    }
}

requests.post(url='http://' + ngsild_cb_url + '/ngsi-ld/v1/entities', data=json.dumps(payload), headers=headers)

payload = {
    'id': 'urn:ngsi-ld:LowLevelOrchestrator:01',
    'type': 'LowLevelOrchestrator',
    'domain': {
        'type': 'Relationship',
        'object': 'urn:ngsi-ld:Domain:IQB'
    },
    'orchestrationType': {
        'type': 'Relationship',
        'object': 'urn:ngsi-ld:OrchestrationType:Kubernetes'
    }
}

requests.post(url='http://' + ngsild_cb_url + '/ngsi-ld/v1/entities', data=json.dumps(payload), headers=headers)

ie_ids = ['aerios-2-jms6qnflylil-master-0', 'aerios-2-jms6qnflylil-node-0', 'aerios-2-jms6qnflylil-node-1', 'aerios-2-jms6qnflylil-node-2']
internal_ips = ['10.0.0.219', '10.0.0.186', '10.0.0.238', '10.0.0.194']

for i in range(4):
    payload = {
        'id': 'urn:ngsi-ld:InfrastructureElement:' + ie_ids[i],
        'type': 'InfrastructureElement',
        'domain': {
            'type': 'Relationship',
            'object': 'urn:ngsi-ld:Domain:IQB'
        },
        'internalIpAddress': {
            'type': 'Property',
            'value': internal_ips[i]
        },
        'macAddress': {
            'type': 'Property',
            'value': ''
        },
        'lowLevelOrchestrator': {
            'type': 'Relationship',
            'object': 'urn:ngsi-ld:LowLevelOrchestrator:01'
        },
        'cpuCores': {
            'type': 'Property',
            'value': -1
        },
        'currentCpuUsage': {
            'type': 'Property',
            'value': -1
        },
        'ramCapacity': {
            'type': 'Property',
            'value': -1
        },
        'availableRam': {
            'type': 'Property',
            'value': -1
        },
        'currentRamUsage': {
            'type': 'Property',
            'value': -1
        },
        'avgPowerConsumption': {
            'type': 'Property',
            'value': -1
        },
        'currentPowerConsumption': {
            'type': 'Property',
            'value': -1
        },
        'realTimeCapable': {
            'type': 'Property',
            'value': False
        },
        'cpuArchitecture': {
            'type': 'Relationship',
            'object': 'urn:ngsi-ld:CpuArchitecture:x64'
        },
        'operatingSystem': {
            'type': 'Property',
            'value': 'Fedora CoreOS 35.20220424.3.0'
        },
        'infrastructureElementTier': {
            'type': 'Relationship',
            'object': 'urn:ngsi-ld:InfrastructureElementTier:Cloud'
        },
        'infrastructureElementStatus': {
            'type': 'Relationship',
            'object': 'urn:ngsi-ld:InfrastructureElementStatus:Ready'
        },
        'location': {
            'type': 'GeoProperty',
            'value': {
                'type': 'Point',
                'coordinates': [21.017532, 52.237049]
            }
        },
        #add this for trustmanager
        'trustScore': {
            'type': 'Property',
            'value':  -1
        },

        #add this for trustmanager
        'trustScoreLastUpdate': {
            'type': 'Property',
            'value':  ''
        }
    }

    requests.post(url='http://' + ngsild_cb_url + '/ngsi-ld/v1/entities', data=json.dumps(payload), headers=headers)

print("Entitities created succesfully")

# TODO add InfrastructureElementStatus, InfrastructureElementTier, CpuArchitecture entities
