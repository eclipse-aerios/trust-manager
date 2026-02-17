import time
import uvicorn
import schedule
import threading
import configparser
from fastapi import FastAPI, Request
from trustmanager import TrustManager

def run_calculation(stop_event):
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    
    ### Setup & Configuration Variables
    config = configparser.ConfigParser()
    config.read('configs/manager.ini')

    # General Parameters
    port = int(config["General"].getint("port")) or 3000
    storageName = config["General"].get("storageName") or "scores"
    storageReset = config["General"].get("storageReset") == "yes"
    
    # Connections Parameters
    orion = config['Connections'].get('ngsild_cb_url')
    domain = config["Connections"].get("domain")
    iota_api_url = config['Connections'].get('iota_api_url','')
    iota_node_url = config['Connections'].get('iota_node_ip','')
    log_file_port = config['Connections'].get('log_file_port')

    # Trust Algorithm Parameters
    scoreInterval = float(config['TrustAlgorithm'].getfloat('scoreInterval')) or 5
    healthPenalty = float(config['TrustAlgorithm'].getfloat('healthPenalty')) or 0.1
    relWeight = float(config["TrustAlgorithm"].getfloat("ReliabilityWeight")) or 0.25
    secWeight = float(config["TrustAlgorithm"].getfloat("SecurityWeight")) or 0.5
    repWeight = float(config["TrustAlgorithm"].getfloat("ReputationWeight")) or 0.25
    relInterval = float(config['TrustAlgorithm'].getfloat('reliabilityInterval')) or 5
    repInterval = float(config['TrustAlgorithm'].getfloat('reputationInterval')) or 5
    priorityThreshold = float(config["TrustAlgorithm"].getfloat("priorityThreshold")) or 3
    notificationThreshold = float(config["TrustAlgorithm"].getfloat("notificationThreshold")) or 4
    
    # Sub-Scores Calculation Parameters
    relParams = dict(config["ReliabilityScore"].items())
    secParams = dict(config["SecurityScore"].items())
    repParams = dict(config["ReputationScore"].items())
    
    # Trust Manager Initialization
    manager = TrustManager(
        dict({
            "name": storageName,
            "reset": storageReset
        }),
        dict({
            "healthPenalty":healthPenalty,
            "weights":{
                "reliability":relWeight,   
                "security":secWeight,   
                "reputation":repWeight   
            },
            "params":{
                "reliability":relParams, 
                "security":secParams,
                "reputation":relParams
            }
        }))
    
    # Server Initialization
    app = FastAPI()

    # Server APIs Setup
    ### Trust Algorithm APIs
    @app.post('/calculate')
    async def topsis_calculation(request:Request):
        args = await request.json()
        try:
            rankings, closeness = manager.trust.calculate_topsis(args["alternatives"],args["weights"] if "weights" in args else {})
            return {"rankings": rankings.tolist(), "scores": closeness.tolist()}
        except KeyError:
            return {"error": "Invalid Arguments Provided"}
        except ValueError as ve:
            return {"error": str(ve)}
        except Exception as e:
            return {"error": str(e)}
        
    @app.get('/weights')
    def get_weights():
        return manager.weights

    ## Reliability Score (Interval) [0, 1] - Normalization Check
    ## Security Score (Real Time) [1, 5] -*-> [0, 1] normalization (?)
    ## Reputation Score (Interval) [1, 5] -*-> [0, 1] normalization  (?)
    # NOTICE: Trust Score = 
    #    + relWeight * Reliability Score 
    #    + secWeight * Security Score 
    #    + repWeight * Reputation Score
    #    - penalty * length(Self-Health Events) -> ?? TBD       
    
    ## Manager Security Score APIs 
    ## NOTICE: Push notifications to this endpoint from Suricata events
    # TODO: Set threshold triggers in configuration !!! -> DONE

    # FIXME: Trust Calculcation Trigger #1: Interval of X minutes (reset notifications)
    ## Manager Trust Score Job <= TRUST SCORE INTERVAL
   
    schedule.every(scoreInterval).minutes.do(manager.update_trust_scores,orion=orion, iota=iota_api_url, node=iota_node_url)
    
    @app.put('/notification')
    async def handle_notification(request:Request):
        data = await request.json()
        print(data)
        id = ""
        if isinstance(data, list):
            #id = data[0]["node_name"]
            id= domain + ":" + data[0]["mac"].replace(":", "")
        elif isinstance(data, dict):
            #id = data["node_name"]
            id = domain + ":" + data["mac"].replace(":", "")
        
        secScore = manager.calculate_security_score(data,domain)
        print("secScore:", secScore)
        #id = "MyDomain:fa163e32c6ee"
        print("notification id: ",id)
        # FIXME: Trust Calculcation Trigger: Number of notification requests done in X minutes (reset notifications, reset calculation interval)
        if id:
            storage = manager.storage.read_item(id)
            if storage["notifications"] > notificationThreshold:
                manager.update_trust_score(id,orion,iota_api_url,iota_node_url)
            # FIXME: Trust Calculcation Trigger: Events with priority Y+ in the X minutes (reset calculation interval)
            #max_priority = max(data, key=lambda x: x["priority"])
            #elif isinstance(data, dict):
            max_priority = data["priority"]
            #if max_priority["priority"] > priorityThreshold:
            if max_priority >= priorityThreshold:
                manager.update_trust_score(id,orion,iota_api_url,iota_node_url)  
        return secScore
    
    ## NOTICE: Register Health Events (Bad News) received in this API 
    # TODO: Reset events weekly, these will refer to bad events happening the last week -> Whenever we calculate the reputation score, these should be reset 
    # TODO: Ask partners for the payload of the API, we expect the ID of the IE for each health event pushed here
    @app.post('/health')
    # Node -> /health ==> Bad thing happened, keep track of the event and how many events have been posted to this API
    async def handle_health(request:Request):
         data =  await request.json()
         print("test")
         print(data)
         #if list count and save to storage
         if isinstance(data, list):
            #id = data[0]["node_name"]
            id = domain + ":" + data[0]["mac_address"].replace(":", "")
            #storage = manager.storage.read_item(data[0]["node_name"])
            storage = manager.storage.read_item(id)
            print(storage)
            alertsNumber = len(data)
            if "health_events" not in storage:
                storage["health_events"] = 0  # Initialize if missing
            manager.storage.write_item({"health_events":storage["health_events"]+alertsNumber},id)
         # If jsonobject
         elif isinstance(data, dict):
            #id = data["node_name"]
            id = domain + ":" + data["mac_address"].replace(":", "")
            storage = manager.storage.read_item(id)
            print(storage)
            if "health_events" not in storage:
                storage["health_events"] = 0  # Initialize if missing
            manager.storage.write_item({"health_events":storage["health_events"]+1},id)
            ##for mvp2
            manager.update_trust_score(id,orion,iota_api_url,iota_node_url)
         else:
            print("Unknown JSON type")
         #storage = manager.storage.read_item(data["id"])
         #manager.storage.write_item({"health_events":storage["health_events"]+1},data["id"])
         return "Health event registered!"
      
    ## Manager Reliability Score Job (done)
    
    schedule.every(relInterval).minutes.do(manager.calculate_reliability_scores,orion=orion)
   

    #manager.calculate_reliability_scores(orion)
    ## Manager Reputation Score Job 
    ## TODO: Ask partners for the log file API to use (Method, URL, Payload)
   
    schedule.every(repInterval).days.do(manager.calculate_reputation_scores,orion=orion, port=log_file_port)
    manager.calculate_reliability_scores(orion)
    #manager.calculate_reputation_scores(orion,log_file_port)
    #manager.init_security_score(orion)
    #manager.update_trust_scores(orion,iota_api_url,iota_node_url)
    #print(f"self security port: {log_file_port}")
    stop_event = threading.Event()
    scheduler_thread = threading.Thread(target=run_calculation, args=(stop_event,))
    scheduler_thread.daemon = True
    scheduler_thread.start()

    
    ## Start Trust Manager Server 
    try:
        print(f"Starting Trust Manager on http://localhost:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        #manager.calculate_reputation_scores(orion,log_file_port)
    except KeyboardInterrupt:
        stop_event.set()#
        scheduler_thread.join()
