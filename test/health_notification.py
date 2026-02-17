import json
import requests

alerts_file = 'self-healing-alerts.json'
#alerts_file = 'self-healing-alerts_value.json'
url = 'http://localhost:3002/health'
# Read the JSON data from the file
with open(alerts_file, 'r') as file:
    data = json.load(file)

# Send the POST request with the JSON data
try:
    response = requests.post(url, json=data)

    # Check if the request was successful
    if response.status_code == 200:
        print("Security events sent successfully!")
        #print("Security Score:",response.text)
    else:
        print(f"Failed to send data. Status code: {response.status_code}, Response: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
