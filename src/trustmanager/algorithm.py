import numpy as np

class TrustAlgorithm:
    """
    ### Trust Algorithm Class
     Provides functionalities for calculating the Trust Score.
    """

    def topsis(self,decision_matrix, weights, impacts):
        """
        Perform TOPSIS method for multi-criteria decision making.
        
        Parameters:
        decision_matrix (numpy array): The decision matrix (alternatives x criteria)
        weights (list): The weights for each criterion
        impacts (list): The impact of each criterion ('positive' or 'negative')
        
        Returns:
        rankings (numpy array): The ranking of alternatives
        relative_closeness (numpy array): The relative closeness to the ideal solution
        """
        # Step 1: Normalize the decision matrix
        norm_matrix = decision_matrix / np.sqrt((decision_matrix**2).sum(axis=0))
        
        # Step 2: Apply the weights to the normalized decision matrix
        weighted_matrix = norm_matrix * weights
        
        # Step 3: Determine the ideal and negative-ideal solutions
        ideal_solution = np.zeros(weighted_matrix.shape[1])
        negative_ideal_solution = np.zeros(weighted_matrix.shape[1])
        
        for i in range(weighted_matrix.shape[1]):
            if impacts[i] == '+':
                ideal_solution[i] = np.max(weighted_matrix[:, i])
                negative_ideal_solution[i] = np.min(weighted_matrix[:, i])
            elif impacts[i] == '-':
                ideal_solution[i] = np.min(weighted_matrix[:, i])
                negative_ideal_solution[i] = np.max(weighted_matrix[:, i])
            else:
                raise ValueError("Impact must be either '+' or '-'.")
        
        # Step 4: Calculate the distance to the ideal and negative-ideal solutions
        distance_to_ideal = np.sqrt(((weighted_matrix - ideal_solution)**2).sum(axis=1))
        distance_to_negative_ideal = np.sqrt(((weighted_matrix - negative_ideal_solution)**2).sum(axis=1))
        
        # Step 5: Calculate the relative closeness to the ideal solution
        relative_closeness = distance_to_negative_ideal / (distance_to_ideal + distance_to_negative_ideal)
        
        # Step 6: Rank the alternatives
        rankings = np.argsort(-relative_closeness) + 1
        
        return rankings, relative_closeness

    def calculate_topsis(self, alternatives, weights={}):
        """
        ### Calculate TOPSIS Scores

        Calculate the topsis scores of given alternatives and their weights.
        
        :param `alternatives` (dict): Alternative decision values
        :param `weights` (dict): Weight values for decision
        :return `ranks` (arr): Ranking scores for alternatives
        """
        # Alternatives Array Check
        if len(alternatives) == 0:
            raise Exception("Alternatives tables cannot be empty")

        # Weight Values & Impacts Check
        weightSum = 0
        for w in weights.keys():
            if weights[w]["impact"] != "+" and weights[w]["impact"] != "-":
                raise Exception("Invalid impact value at",w,weights[w])
            weightSum += float(weights[w]["weight"])
        
        # Weight Sum & Length Check
        if weightSum != 1 :
            raise Exception("Weight must sum to 1")
        for x in alternatives:
            if len(x) != len(weights):
                raise Exception("Invalid length for alternatives and weights")

        # Extract Weight Values & Impacts
        weightValues = [float(weights[x]["weight"]) for x in weights]
        weightImpacts = [weights[x]["impact"] for x in weights]

        # Perform TOPSIS evaluation
        return self.topsis(np.array(alternatives),weightValues, weightImpacts)
    
    # FIXME: Add impact factoring to the weights (minor feature)
    def calculate_wsum(self, values, weights):
        """
        ### Calculate Weighted Sum Score

        Calculate the elapsed time since the provided previous time.
        
        :param `values` (array): Values to sum
        :param `weights` (array): Weight values for decision
        :return `ranks` (arr): Ranking scores for alternatives
        """
        # Values or Weights Array Check
        if len(values) == 0 or len(weights) == 0 :
            raise Exception("Values or weights cannot be empty")
                
        # Values & Weights Array Check
        if len(values) != len(weights):
            raise Exception("Values & Weights must be equal in length")

        result = 0
        for i in range(len(values)):
            result += values[i]*weights[i]
        return result
    
