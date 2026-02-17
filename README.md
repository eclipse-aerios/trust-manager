# aeriOS Trust Manager

The Trust Manager monitores and evaluates the trustworthiness of an Infrastructure Element of the aeriOS Cloud-Edge-IoT continuum.

## Overview
This repository contains the source code for the Trust Manager which interacts with the NGSI-LD Context Broker, Self-awareness, Self-security and Self-healing in order to **calculate a trust score** for all the Infrastucture Elements that compose an aeriOS Domain.

The project's architecture is defined by the following components:

1. [Self-awareness](./): This is the self-capability that allows to get real-time information about the status of the IE. It gathers information about the IE and submits it to the associated Data Fabric/Context broker. This module can Obtain parameters such as CPU data, RAM data etc.
2. [Trust Manager](./src/trustmanager/manager.py): A component that calculates the Trustworthness of IE based on TOPSIS method.
3. [NGSI-LD Context Broker](./docker-compose.yaml#L4): A component that allows managing the lifecycle of device entities including updates, queries, registrations and subscriptions. Included in the Docker Compose as a Docker image.


## Trust Score calculation

In order to calculate the final trust score (between 0 and 1) of an IE, three sub scores are calculated:

1. **Reliability Subscore**:  Evaluates the performance and stability of Infrastructure Elements 
2. **Security Subscore**: Represents the system's short-term state regarding exposure to cyber threats
3. **Reputation Subscore**: Represents the system's long-term state regarding exposure to cyber threats


The overall score (TS) is calculated using the following formula:

```
TS = (Wrep × SBrep) + (Wsec × SBsec) + (Wrel × SBrel) − Penalty
```

Where:

- **Wrep**, **Wsec**, **Wrel**: These represent the weights assigned to the Reputation, Security, and Reliability sub-scores, respectively.
- **SBrep**, **SBsec**, **SBrel**: These are the individual sub-scores for Reputation, Security, and Reliability.
- **Penalty**: This is a deduction applied based on the frequency of critical self-healing alerts, reflecting the stability of the IE system.

### Reliability Score
The communications steps to calculate the **Reliability score** are the following:

1. The Self-awareness retrieves monitoring data from the device, depending on the configurations defined. These data includes cpu, memory, etc.

2. After a specified interval the Self-awareness updates the NGSI-LD entity of the IE on the NGSI-LD Context Broker with the collected data.

3. The Trust Manager periodically collects data for each IE.

4. The Trust Manager calculates the score/rank of each IE using the Topsis Method.

5. The Trust Manager updates the score in the Context Broker and introduces a message into the IOTA tangle that contains the score.

### Security Score
The communications steps to calculate **Security score** are the following:

1.	The Self-security module includes an API designed to send real-time alerts to the Trust Manager, each of which has a severity priority ranging from 1 (most severe) to 5 (least severe).

2.	The Trust Manager calculates the average priority value of these alerts and normalizes it to a scale of 0 to 1.

3.	The normalized value becomes the security sub-score.

### Reputation Score
The communications steps to calculate **Reputation score** are the following:

1.  The Self-security module provides alerts generated over a one-week period via an API.

2.	The Trust Manager retrieves these alerts, calculates the average priority value, and normalizes it to 0 to 1.

3.	This value forms the reputation sub-score.


## Local development

### Installation ⚡

Execute the following command to install the requirements:

```console
pip install -r requirements/manager.txt
```

### Usage ⚡

Execute the following command to run the manager:

```console
python src/trustmanager/manager.py
```

Configure the manager settings in the [config](./configs/manager.ini) file.

### Setup local environment for testing and dev

Execute the Docker compose command to create the Orion containers:

```console
docker compose -f test/docker-compose_final_local.yaml up -f
```

Execute the following script to initialize Orion-ld CB with the data model of aeriOS

```console
python test/entities_creation_script.py
```

## APIs

> **GET** http://localhost:3000/weights

Request the weights configured in the Trust Manager:

### Example

- **Response Body**

```json
{
  "cpucores": {
    "impact": "+",
    "weight": "0.2"
  },
  "currentcpuusage": {
    "impact": "-",
    "weight": "0.2"
  },
  "ramcapacity": {
    "impact": "+",
    "weight": "0.1"
  },
  "availableram": {
    "impact": "+",
    "weight": "0.25"
  },
  "currentramusage": {
    "impact": "-",
    "weight": "0.25"
  }
}
```

> **POST** http://localhost:3000/calculate

Request from the Trust Manager to perform a score evaluation of the altervatives provided. The request body can contain two parameters:

1. `alternatives` (int[][]): The array containing the values of each alternative
2. `weights` (list) _[Optional]_: A list containing the weights for the trust score calculation

### Example

- **Request Body**

```json
{
  "alternatives": [
    [250, 16, 12, 5],
    [200, 16, 8, 3],
    [300, 32, 16, 4],
    [275, 32, 8, 4],
    [225, 16, 16, 2]
  ],
  "weights": {
    "cpu": {
      "impact": "+",
      "weight": 0.25
    },
    "ram": {
      "impact": "+",
      "weight": 0.25
    },
    "lel": {
      "impact": "-",
      "weight": 0.25
    },
    "bel": {
      "impact": "+",
      "weight": 0.25
    }
  }
}
```

- **Response Body**

```json
{
  "rankings": [4, 3, 1, 2, 5],
  "scores": [
    0.5342768571821003, 0.4223512916762782, 0.5776487083237218,
    0.7959914251761436, 0.07272619042582074
  ]
}
```

