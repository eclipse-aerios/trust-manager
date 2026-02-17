import json
import os
import uuid
import operator
from prettytable import PrettyTable

class LocalStorage:
    """
    ### Local Storage Class

    Provides functionalities for storing a dictionaries of data.
    In the context of the aeriOS project, these are:
    - Reliability Score (hardware metrics)
    - Security Score (network threats, severity/priority)
    - Reputation Score (weekly historical data from self-sec & self-heal)

    :param `name` (str): name of the storage (used as the filename for the JSON file)
    :param `reset` (bool): If True, resets/truncates the database when the class is created.
    """
    
    def __init__(self, name, reset=False):
        self.name = name
        self.filepath = f"{name}.json"
        if reset or not os.path.exists(self.filepath):
            self.db = {"keys": [], "data": {}}
            self.__save_db()
        else:
            self.db = self.__load_db()

    def __load_db(self):
        """Loads the database from the JSON file."""
        with open(self.filepath, 'r') as file:
            return json.load(file)

    def __save_db(self):
        """Saves the current state of the database to the JSON file."""
        with open(self.filepath, 'w') as file:
            json.dump(self.db, file, indent=4)

    def __update_keys(self, data):
        """
        Updates the global `keys` list with unique parameters from the provided data.
        
        :param data: The dictionary to extract keys from.
        """
        for key in data.keys():
            if key not in self.db["keys"]:
                self.db["keys"].append(key)
    
  
    
    def write_item(self, data, key=""):
        """
        Writes a new item to the storage. The key for the item is by default randomly generated, and the global `keys` list is updated to track unique parameters in the data.
        
        :param data: The dictionary of data to store under a random ID.
        """
        if key == "":
            key=str(uuid.uuid4())
        self.__update_keys(data)
        if key in self.db["data"]:
            self.db["data"][key].update(data)
        else:
            self.db["data"][key] = data
        self.__save_db()

        return key

    def read_item(self, key):
        """
        Reads and returns the data associated with the given random key.
        
        :param key: The random key of the item to read.
        :return: The data associated with the key, or None if the key does not exist.
        """
        return self.db["data"].get(key, None)

    def delete_item(self, key):
        """
        Deletes an item from the storage.
        
        :param key: The random key of the item to delete.
        :return: True if the item was deleted, False if the key does not exist.
        """
        if key in self.db["data"]:
            # Remove the data associated with the key
            del self.db["data"][key]
            
            # Save changes to the JSON file
            self.__save_db()
            
            return True
        else:
            return False

    def table(self,null="-"):
        """
        ## Table print the storage

        Prints all the stored data in a tabular format using PrettyTable. Ensures that
        each row has the same number of values by filling missing data with empty strings.

        :param `null` (str): Placeholder for null values.
        """
        table = PrettyTable()
        table.field_names = ["key"] + self.db["keys"]
        for key, item in self.db["data"].items():
            row = [key]
            
            for field in self.db["keys"]:
                row.append(item.get(field, null))
            
            table.add_row(row)
        return table
    
    def list_keys(self):
        """
        Lists all unique parameter names in the database (tracked in `keys`).
        
        :return: A list of unique parameter names.
        """
        return self.db["keys"]

    def filter_items(self, conditions):
        """
        Filters and returns the data that match the given dynamic conditions.

        :param conditions: A dictionary where keys are parameter names and values are tuples/lists of the form (operator, value). Supported operators: ==, !=, >, <, >=, <=.
        :return: A dictionary of matching items, where keys are the random data keys and values are the data dictionaries.
        """
        operators = {
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            "<": operator.lt,
            ">=": operator.ge,
            "<=": operator.le
        }
        result = {}
        for key, item in self.db["data"].items():
            match = True  # Flag to check if all conditions are satisfied
            for cond_key, (op, cond_value) in conditions.items():
                if cond_key in item:
                    if not operators[op](item.get(cond_key), cond_value):
                        match = False
                        break
                else:
                    match = False
                    break
            if match:
                result[key] = item
        return result
