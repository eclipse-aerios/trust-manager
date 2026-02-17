import json
import time
import requests
from datetime import datetime
from trustmanager.algorithm import TrustAlgorithm
from trustmanager.storage import LocalStorage

class TrustManager:
    """
    ### Trust Manager Class

    Provides functionalities for monitoring Trust Agents' through the Orion Broker and updating their Trust Score.
    
    :param `storage` (dict): Storage file name and reset options
    :param `algorithm` (dict): Trust algorithm configurations
    """
    # TODO: Initialize storage inside Trust Manager 
    # FIXME: We need to have rel,sec, rep and finally trust calculation methods 
    # FIXME: We can remove orion and iota data from here and use them in the scheduler functions 
    def __init__(self,storage,algorithm):
        self.trust = TrustAlgorithm()
        self.storage = LocalStorage(storage["name"],storage["reset"])
        self.weights = dict(algorithm["weights"])
        self.penalty = algorithm["healthPenalty"]
        self.scores = {}
        for param in algorithm["params"]:
            self.scores[param] = {}
            for key, value in algorithm["params"][param].items():
                impact = value[:1] if value.startswith(("+", "-")) else "+"
                weight = value[1:] if value.startswith(("+", "-")) else value
                self.scores[param][key] = {
                    "impact": impact,
                    "weight": weight
                }

    
    def calculate_elapsed(self,previous_time):
        """
        ### Elapsed Time

        Calculate the elapsed time since the provided previous time.
        
        :param `previous_time` (int): Previous time to calculate elapsed time in seconds
        :return `elapsed_time` (int): Elapsed time difference in seconds
        """
        current_time = time.time()
        elapsed_time = current_time - previous_time
        return elapsed_time

    def calculate_reliability_scores(self,orion):
        """
        ### Calculate & Update localstorare reliability Score

        Calculate the TOPSIS score of the IE and update their values in the localstorage.
        """
        print('[TrustManager] Starting reliability score calculation')
        IE_IDs = self.__get_all_orion_entities(orion)
        agent_ids = []
        decision_matrix = []
        #print(self.scores["reliability"])
        #print(IE_IDs)
        for agent_id in IE_IDs:
            print(f'[TrustManager] Collected data about {agent_id}')
            values = []
            agent = self.__get_entity(orion,agent_id)
            for key in agent.keys(): # type: ignore
                #print(key + "\n")
                if key.lower() in self.scores["reliability"]:
                    values.append(agent[key]["value"]) # type: ignore
            agent_ids.append(agent_id)
            decision_matrix.append(values)

        if len(decision_matrix)== 1:
            # Assign reliability score of 1.0 for the single agent (100% as only choice)
            print('[TrustManager] Only one agent found. Assigning default reliability score of 1.0')
            self.storage.write_item({"reliability": 0.8}, agent_ids[0])
            return

        print(f'[TrustManager] Decision Matrix:', decision_matrix)
        rankings, relative_closeness = self.trust.calculate_topsis(decision_matrix,self.scores["reliability"])
        for i, agent_id in enumerate(agent_ids):
            print(agent_id, relative_closeness[i])
            self.storage.write_item({"reliability":relative_closeness[i]},agent_id)

        print(f'[TrustManager] Alternatives Rankings: ', rankings)
        print(f'[TrustManager] Ideal Solution Closeness: ', relative_closeness)
   
    def calculate_security_score(self,data,domain):
        """
        ### Calculate & Update localstorare security Score

        Calculate the security score of the IE and update their values in the localstorage.
        """
        print('[TrustManager] Starting security score calculation')
        priority_score = 0
        security_score = 0
        IE_ID = ""
        #if list count and save to storage
        if isinstance(data, list):
            for event in data:
                priority_score += event["priority"]
                #IE_ID = event["node_name"]
                IE_ID = ""+domain+":" +event["mac"].replace(":", "")
        
            security_score = priority_score / len(data)
        elif isinstance(data, dict):
            security_score = data["priority"]
            IE_ID = ""+domain+":" + data["mac"].replace(":", "")
        #normalized security score
        else:
            print("Unknown JSON type")
        print("sec sb id ", IE_ID)
        security_score= security_score
        security_score = security_score/5
        print("Security Score:",security_score)
        #IE_ID= ""
        if IE_ID:
            storage = self.storage.read_item(IE_ID)
            if "notifications" in storage:
                print("Key 'notifications' exists!")
                self.storage.write_item({"security":security_score, "notifications":storage["notifications"] + 1},IE_ID)
            else:
                print("Key 'notifications' does not exist!")
                self.storage.write_item({"security":security_score, "notifications":1},IE_ID)
        return security_score

    def init_security_score(self,orion):
        
        security_score = 5/5
        print("Security Score:",security_score)
        IE_IDs = self.__get_all_orion_entities(orion)
        for IE_ID in IE_IDs:
            if IE_ID:
                storage = self.storage.read_item(IE_ID)
                if "notifications" in storage:
                    print("Key 'notifications' exists!")
                    self.storage.write_item({"security":security_score, "notifications":storage["notifications"] + 1},IE_ID)
                else:
                    print("Key 'notifications' does not exist!")
                    self.storage.write_item({"security":security_score, "notifications":1},IE_ID)
    
    
    def calculate_reputation_scores(self, orion, port):
        """
        ### Reputation Score

        Update the reputation score of an IE.
        
        :param `orion` (str): Orion broker url
        """
        # IE_IDs = self.__get_all_orion_entities(orion)
        # print("Collected IDs:"+str(IE_IDs.keys()))
        # for id, ip in IE_IDs.items():
        #     reputation = 0
        #     print(id,ip)
        #     try:
        #         print("self-security api")
        #         print('http://' + ip + ':' + port + '/events')
        #         response = requests.request(method="GET",url='http://' + ip + ":"+ port + '/events', headers={"accept":"application/json"})
        #         response.raise_for_status()
        #         #data =response.json()
        #         print(len(response.text))
        #        # data = response.json()
        #         #for event in data:
        #         #    reputation += event["priority"]
        #        # reputation = reputation/len(data)
        #        # reputation = reputation/5
        #         #self.storage.write_item({"reputation":reputation, "health_events":0},id)
        #     except:
        #         print("error fetching data")
        # try:
        #     IE_IDs = self.__get_all_orion_entities(orion)
        #     print("Collected IDs:"+str(IE_IDs.keys()))
        #     for id, ip in IE_IDs.items():
        #         reputation = 0
        #         try:
        #             # FIXME: Need feedback on the reputation log file API (Method, URL, Response Payload)
        #             print('http://' + ip + ":"+ port + '/events')
        #             #print('http://localhost:' + port + '/events')
        #             response = requests.request(method="GET",url='http://' + ip + ":"+ port + '/events', headers={"accept":"application/json"})
        #             #response = requests.request(method="GET",url='http://localhost:' + port + '/events', headers={"accept":"application/json"})
        #             # response = requests.request(method="GET",url='http://localhost:9000/events', headers={"accept":"application/json"})
        #             #test url
        #             #response = requests.request(method="GET",url='http://localhost:8083/self-security-alerts.json', headers={"accept":"application/json"})
                    
        #             response.raise_for_status()
        #             data = response.json()
        #             for event in data:
        #                 reputation += event["priority"]
        #             print(reputation)
        #             reputation = reputation/len(data)
        #             #normalize reputation score
        #             reputation = reputation/5
        #             # FIXME: Are we going to have weight when measuring reputation ?
        #             self.storage.write_item({"reputation":reputation, "health_events":0},id)
        #         #except requests.exceptions.RequestException as error:
        #         except:
        #             print("get reputation logs error")
        # except:
        #     print("generar error")
        IE_IDs = self.__get_all_orion_entities(orion)
        print("Collected IDs:"+str(IE_IDs.keys()))
        for id, ip in IE_IDs.items():
            reputation = 0
            try:
                # FIXME: Need feedback on the reputation log file API (Method, URL, Response Payload)
                #print(id)
                response = requests.request(method="GET",url='http://' + ip + ":"+ port + '/events', headers={"accept":"application/json"})
                # response = requests.request(method="GET",url='http://localhost:9000/events', headers={"accept":"application/json"})
                #test url
                #response = requests.request(method="GET",url='http://localhost:8083/self-security-alerts.json', headers={"accept":"application/json"})
                print('http://' + ip + ":"+ port + '/events')
                #response.raise_for_status()
                response.raise_for_status()
                data = response.json()
                for event in data:
                    reputation += event["priority"]
                print("reputation sum", reputation)
                #reputation = reputation/len(data)
                if(len(data)>0):
                    reputation = reputation/len(data)
                else:
                    reputation = 0
                #normalize reputation score
                #reputation=3
                reputation= reputation
                reputation = reputation/5
                print(f"reputation score: {reputation}")
                # FIXME: Are we going to have weight when measuring reputation ?
                self.storage.write_item({"reputation":reputation, "health_events":0},id)
            except Exception as error:
                print(f"[TrustManager] Error getting reputation file {str(error)}")
                
    def calculate_trust_score(self, id):
        """
        ### Calculate Trust Score

        Calculate the Trust Score of an IE using the stored subscores.
        
        :param `id` (str): Id of device to calculate trust score
        """
        storage = self.storage.read_item(id)
        trust_score = 0
        for param in storage:
            if param in self.weights.keys():
                trust_score += self.weights[param] * storage[param]
        if "health_events" in storage.keys() and storage["health_events"] > 0:
            trust_score -= self.penalty * storage["health_events"]
        if trust_score < 0:
            trust_score = 0
        print(f"INFO:\t  Calculated trust score for {id}: {trust_score}")
        return trust_score
    
    def update_trust_score(self, id, orion="", iota="", node=""):
        """
        ### Update Trust Score

        Update the Trust Scores of all IEs in storage, orion and iota.
        
        :param `orion` (str): Url of the orion broker
        :param `iota` (str): Url of the Iota network
        :param `node` (str): Id of the Iota node
        """

        # Get the current timestamp
        current_timestamp = datetime.now().isoformat()

        # Print the current timestamp
        print("Current Timestamp:", current_timestamp)
        storage = self.storage.read_item(id)
        if storage != None:
            trust_score = self.calculate_trust_score(id)
            self.storage.write_item({"trust":trust_score,"trust_last_update":current_timestamp,"notifications":0},id)
            #self.storage.write_item({"trust":trust_score,"notifications":0},id)
            
        if orion != "": 
            self.update_orion_score(orion,id,score=trust_score,time=current_timestamp)
        if iota != "" and node !="":
            self.update_iota_score(iota,node,id,score=trust_score)
    
    def update_trust_scores(self, orion="", iota="", node=""):
        """
        ### Update all Trust Score

        Update the Trust Scores of all IEs in storage, orion and iota.
        
        :param `orion` (str): Url of the orion broker
        :param `iota` (str): Url of the Iota network
        :param `node` (str): Id of the Iota node
        """
        IE_IDs = self.__get_all_orion_entities(orion)
        for id in IE_IDs:
            data = self.storage.read_item(id)
            if data != None:
                current_timestamp = datetime.now().isoformat()
                trust_score = self.calculate_trust_score(id)
                self.storage.write_item({"trust":trust_score,"trust_last_update":current_timestamp,"notifications":0},id)
                #self.storage.write_item({"trust":trust_score,"notifications":0},id)
            if orion != "": 
                self.update_orion_score(orion,id,score=trust_score,time=current_timestamp)
            if iota != "" and node !="":
                print("update IOTA")
                try:
                    self.update_iota_score(iota,node,id,score=trust_score)
                except Exception as e:
                    print(f"error: {str(e)}")
            else:
                print("IOTA url not found")
        
    # ORION INTERACTIONS
    def __get_all_orion_entities(self, orion):
        """
        ### Get All Orion Entities

        Request all entities from the Orion broker using their ID.
        
        :param `orion` (str): Url of the Orion broker
        """
        print("[TrustManager] Requesting NGSI-LD entities...")
        url = 'http://'+orion+'/ngsi-ld/v1/entities'
        headers = {
            'Accept': 'application/json'
        }
        params = {
            'type': 'InfrastructureElement',
            'local': 'true',
            'options': 'keyValues',
        }
        response = requests.get(url, headers=headers, params=params)

        print("[TrustManager] Entities retrieved!")
        # Iterate over each entity and print its ID
        IE_IDs= dict()
        for IE in response.json():
            
            entity_id = IE.get('id', None)
            entity_ip = IE.get('internalIpAddress', None)
            #print(f" whole id: {entity_id}")
            if entity_id and entity_ip:
                dmn = entity_id.split(":")[-2]
                ieid = entity_id.split(":")[-1]
                iek = dmn + ':' + ieid
                #print(iek)
                #print(f" domainID: {iek}")
                #IE_IDs[entity_id.split(":")[-1]] = entity_ip
                IE_IDs[iek] = entity_ip
            else:
                print(f"IE for {entity_id} not found!")
        return IE_IDs
    
    def __get_entity(self, orion, id):
        """
        ### Get Orion Entity by ID

        Request an agent entity from the Orion broker using their ID.
        
        :param `orion` (str): Url of the Orion broker
        :param `id` (str): Id of the entity to query
        """
        try:
            print('http://' + orion + '/ngsi-ld/v1/entities/urn:ngsi-ld:InfrastructureElement:' + id)
            response = requests.request(method="GET",url='http://' + orion + '/ngsi-ld/v1/entities/urn:ngsi-ld:InfrastructureElement:' + id + '?local=true', headers={"accept":"application/json"})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as error:
            print(f"[TrustManager] Error getting entity {error}")
            return False
                
    def get_orion_data(self, orion):
        """
        ### Get Orion IE Data

        Fetch the data collected by the IE in the Orion Broker.
        
        :param `orion` (str): Url of the Orion broker
        """
        print('[TrustManager] Fetching agent data')
        IE_IDs = self.__get_all_orion_entities(orion)

        agent_data = []
        for agent_id in IE_IDs:
            print(f'[TrustManager] Collected data about {agent_id}')
            agent_data.append(self.__get_entity(orion,agent_id))
        return agent_data    
    
    def update_orion_score(self, orion, id, score,time):
         """
        ### Update Orion Score by ID

        Update the trust score value for a specific IE id in the Orion Broker.
        
        :param `orion` (str): Url of the Orion broker
        :param `id` (str): Id of the IE to update
        :param `score` (float): New score of the IE 
        """
         try:
            # Patch update to Orion Broker 
            response = requests.patch(url='http://' + orion + '/ngsi-ld/v1/entities/urn:ngsi-ld:InfrastructureElement:' + id+ '/attrs', headers= {"content-type":"application/json"}, data=json.dumps({"trustScore":{"type":"Property","value":score}, }))
            response.raise_for_status()
            #response = requests.patch(url='http://' + orion + '/ngsi-ld/v1/entities/urn:ngsi-ld:InfrastructureElement:' + id + '/attrs', headers= {"content-type":"application/json"}, data=json.dumps({"trustScoreLastUpdate":{"type":"Property","value":time}}))
            #response.raise_for_status()
         except requests.exceptions.RequestException as error:
            print(f"[TrustManager] Error updating entity {error}")

    # IOTA INTERACTIONS 
    def update_iota_score(self, iota_api_url, iota_node_url, id, score):
        """
        ### Update Iota Score

        Update trust score values in the Iota Node.

        :param `iota_api_url` (str): Url of the Iota API
        :param `iota_node_url` (str): Url of the Iota node
        :param `id` (str): Id of the relevant IE
        :param `score` (float): New score of the IE 
        """
        try:
            # Post update to Iota Node
            response = requests.post(url='http://' + iota_api_url + '/upload?node=' + iota_node_url, headers= {"content-type":"application/json"}, data=json.dumps({"tag":"trust.score","message":{"score":score, "id":id}}))
            print(response.text)
            response.raise_for_status()
        except requests.exceptions.RequestException as error:
            print(f"[TrustManager] Error updating entity {error}")
    