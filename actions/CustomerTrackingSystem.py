import json
from .utils import Utils

class CustomerTrackingSystem:
    
    def __init__(self, filepath, roi_1, roi_2, dispatcher, entities = None) -> None:
        self.filepath = filepath
        self.roi_1 = roi_1
        self.roi_2 = roi_2
        self.foi = {
            "gender": None,
            "bag": None,
            "hat": None,
            "upper_color": None,
            "lower_color": None,
            "roi1_passages": None,
            "roi1_persistence_time": None,
            "roi2_passages": None,
            "roi2_persistence_time": None
        }
        self.nop = 0
        self.entities = entities
        self.dispatcher = dispatcher

    def update(self):
        """
        Update the internal state of the object based on the provided entities.

        This method processes a list of entities and updates the internal state of the object, including ROI (Region of Interest),
        clothing, and gender information. It iterates through each entity, updating the relevant fields in the 'current_group'
        dictionary.
        In order to properly implement the update logic, taking into account negation, colours and possible placements in the text of the entities related to roi, we have defined two variables to implement this:
        - `current_group` is a dictionary that gets cleared each time clothing or gender-related entities are encountered. This approach ensures correct implementation of logic for negation and color, taking advantage of the fact that in English, adjectives always precede the noun. The management of fields related to ROI entities is more complex, but still managed by the dictionary.
        - `roi` is a flag used to manage the update of ROI fields, where the logic is more complex than in the previous case. The flag is set to True when updating ROI fields and False when processing other types of entities.
        
        Parameters:
        - None

        Returns:
        - bool: True if the update is successful, False otherwise.

        Raises:
        - None
        """
        # Initialize an empty dictionary to store the current group of entities.
        current_group = dict()  
        # Initialize a flag to track whether ROI fields are being updated.
        roi = False
        
        print("=== UPDATE ===")  # Print a header for the update process.

        for entity in self.entities:
            print(f"Entity: {entity['entity']}, Value: {entity['value']}")  # Print information about each entity being processed.

            entity_key = entity['entity']
            entity_value = entity['value']
            
            # Update ROI Fields         
            if self.__update_roi(current_group, roi, entity_key) is False:
                return False
            if entity_key in ["passages", "duration", "place"]:
                roi = True
                neg = False if "negation" in current_group else True
                if not neg:
                    del current_group["negation"]
                current_group[entity_key] = (entity_value, neg) 
            else:                
                roi = False
                current_group[entity_key] = entity_value

            if not roi:
                # Update Clothing Fields
                if "clothing" in entity_key:  
                    if self.__update_clothing(current_group=current_group, entity_value=entity_value) is False:
                        return False
                # Update Gender Field
                elif "gender" in entity_key:
                    self.__update_gender(current_group=current_group, entity_value=entity_value)

        # Update ROI Fields if current_group is not empty - that is, there are ROI entities at the end of the utterance.
        if current_group:
            if self.__update_roi(current_group, update=True) is False:
                return False
                
        return True 

    def filteringJSON(self):
        """
        Filter the JSON data based on the criteria specified in the 'foi' (fields of interest) dictionary.

        This method reads JSON data from the specified file, filters the data based on gender, clothing items (hat and bag),
        upper and lower clothing colors, and ROI-related criteria (ROI and ROI persistence time). The filtered data is then
        returned.

        Parameters:
        - None

        Returns:
        - list: A list of filtered people based on the data of interest (doi).

        Raises:
        - None

        """
        doi = dict()    # Data of Interest Dict

        with open(self.filepath, 'r') as f:
            data = json.load(f)
            doi = data["people"]

            # Filter gender, hat, bag
            foi_gender_hat_bag = {key: value for key, value in list(self.foi.items())[0:3] if value is not None}

            if foi_gender_hat_bag:
                doi = [person for person in data['people'] if all(
                    person[key] == value
                    for key, value in foi_gender_hat_bag.items()
                )]

            # Filter upper_color and lower_color
            foi_color_cloths = {key: value for key, value in list(self.foi.items())[3:5] if value is not None}
            if foi_color_cloths:
                doi = [person for person in doi if all(
                    (person[key] == value) if not isinstance(value, tuple) else
                    (person[key] == value[0]) if value[1] else
                    (person[key] != value)
                    for key, value in foi_color_cloths.items()
                )]

            # Filter roi and roi_persistence_time
            foi_roi = {key: value for key, value in list(self.foi.items())[5:9] if value is not None}
            if foi_roi:
                doi = [person for person in doi if all(
                    (person[key] >= value[0]) if value[1] else (person[key] < value[0]) for key, value in foi_roi.items()
                )]

            self.nop = len(doi)  # Update the number of people after filtering.

            return doi

    def __str__(self) -> str:
        people_string = "people of " + self.foi["gender"] + " gender" if self.foi["gender"] is not None else "people"
        output_string = []
        output_string.append("bag" if self.foi["bag"] is True else "no bag" if self.foi["bag"] is False else None)
        output_string.append("hat" if self.foi["hat"] is True else "no hat" if self.foi["hat"] is False else None)
        if self.foi["upper_color"]:
            if isinstance(self.foi["upper_color"], tuple):
                output_string.append(f'{self.foi["upper_color"][0]} top' if self.foi["upper_color"][1] is True else f'no {self.foi["upper_color"][0]} top' if self.foi["upper_color"][1] is False else None)
            else:
                output_string.append(f'{self.foi["upper_color"]} top')
        if self.foi["lower_color"]:
            if isinstance(self.foi["upper_color"], tuple):
                output_string.append(f'{self.foi["lower_color"][0]} trouser' if self.foi["lower_color"][1] is True else f'no {self.foi["lower_color"][0]} trouser' + " trouser" if self.foi["lower_color"][1] is False else None)
            else:
                output_string.append(f'{self.foi["lower_color"]} trouser')
        if self.foi["roi1_passages"]:
            passages_string = ("once" if self.foi["roi1_passages"][0] == 1 else "twice" if self.foi["roi1_passages"][0] == 2 else f'{self.foi["roi1_passages"][0]} times')
            roi_string = "have stayed at least " + passages_string if self.foi["roi1_passages"][1] is True else "have not stayed at least " + passages_string if self.foi["roi1_passages"][1] is False else None
            
            if self.foi["roi1_persistence_time"]:
                time_string = f'{self.foi["roi1_persistence_time"][0]} seconds' 
                roi_string += " and at least " + time_string if self.foi["roi1_persistence_time"][1] is True else " and not at least " + time_string if self.foi["roi1_persistence_time"][1] is False else None 
            output_string.append(roi_string + " in front of the supermarket")
        if self.foi["roi2_passages"]:
            passages_string = ("once" if self.foi["roi2_passages"][0] == 1 else "twice" if self.foi["roi2_passages"][0] == 2 else f'{self.foi["roi2_passages"][0]} times') 
            roi_string = "have stayed at least " + passages_string if self.foi["roi2_passages"][1] is True else "have not stayed at least " + passages_string if self.foi["roi2_passages"][1] is False else None

            if self.foi["roi2_persistence_time"]:
                time_string = f'{self.foi["roi2_persistence_time"][0]} seconds' 
                roi_string += " and at least " + time_string if self.foi["roi2_persistence_time"][1] is True else " and not at least " + time_string if self.foi["roi2_persistence_time"][1] is False else None 
            output_string.append(roi_string + " in front of the bar")
            
        attributes = [item for item in output_string if item is not None]
        attribute_str = ', '.join(item for item in attributes)
        return f"There are currently {self.nop} {people_string} in the mall that meet the required specifications: {attribute_str}." if attributes else f"There are currently {self.nop} {people_string} in the mall."

    # Private Methods
    def __update_roi(self, current_group, roi = False, entity_key = None, update = False):
        """
        Update Region of Interest (ROI) information based on the provided group and optional parameters.

        Parameters:
        - current_group (dict): The group containing information to update the ROI.
        - roi (bool): Indicates whether to update the ROI.
        - entity_key (str): The key representing the entity type to update within the ROI.
        - update (bool): Indicates whether to force an update.

        Returns:
        - bool: True if the update is successful, False otherwise.

        Raises:
        - None
        """
        if (roi and entity_key in ["color", "clothing"]) or (roi and entity_key in current_group) or update:
            (passages, neg_passages) = (Utils.adverb_to_number(current_group["passages"][0], dispatcher=self.dispatcher), current_group["passages"][1]) if "passages" in current_group else (1, True)
            (time, neg_time) = (Utils.convert_time_to_seconds(current_group["duration"][0], dispatcher=self.dispatcher), current_group["duration"][1]) if "duration" in current_group else (None, None)
            (place, neg_place) = (current_group["place"][0], current_group["place"][1]) if "place" in current_group else (None, None)
            
            if time is not None and neg_place == False:
                neg_time = False
                neg_place = neg_passages
            
            if place is not None:
                if place.lower() == self.roi_1:
                    self.foi["roi1_passages"] = (passages, neg_passages and neg_place)
                    self.foi["roi1_persistence_time"] = (time, neg_time) if neg_time is not None else time
                elif place.lower() == self.roi_2:
                    self.foi["roi2_passages"] = (passages, neg_passages and neg_place)
                    self.foi["roi2_persistence_time"] = (time, neg_time) if neg_time is not None else time
                else:
                    self.dispatcher.utter_message(text=f"My apologies! I don't know if there are " + place.lower() + " in the shopping mall. I can only check the people passing through the " + self.roi_1 + " and the " + self.roi_2 + ".")
                    return False
            else:
                self.dispatcher.utter_message(text=f"My apologies! Please point me somewhere to check. Remember, i can only check the people passing through the " + self.roi_1 + " and the " + self.roi_2 + ".")
                current_group.clear()
                return False
            
            current_group.clear()
            return True
    
    def __update_clothing(self, current_group, entity_value):    
        """
        Update clothing information based on the provided group and entity value.

        Parameters:
        - current_group (dict): The group containing clothing information to update.
        - entity_value (str): The value representing the type of clothing to update.

        Returns:
        - bool: True if the update is successful, False otherwise.

        Raises:
        - None
        """
        neg = not "negation" in current_group
        color = current_group.get("color", None)
        
        current_group.clear()
        
        if color and entity_value in ["top", "trouser"]:
            cloth = "upper_color" if entity_value == "top" else "lower_color"
            self.foi[cloth] = (color, neg)
        elif not color and entity_value in ["hat", "bag"]:
            self.foi[entity_value] = neg
        else:
            self.dispatcher.utter_message(text=f"Could you explain the question better? Remember, i am not able to recognize the colors of hats and bags, only of shirts and pants.")
            return False
        
        return True
        
    def __update_gender(self, current_group, entity_value):
        """
        Update gender information based on the provided group, entity key, and entity value.

        Parameters:
        - current_group (dict): The group containing gender information to update.
        - entity_key (str): The key representing the entity type (e.g., "gender") to update.
        - entity_value (str): The value representing the gender to update.

        Returns:
        - None

        Raises:
        - None
        """
        neg = not "negation" in current_group

        current_group.clear()

        self.foi["gender"] = entity_value if neg is True else "female" if entity_value == "male" and neg is False else "male"
        
        
# if __name__ == '__main__':

#     # foi = {"gender": "male", "hat": False, "bag": False, "upper_color": "blue", "lower_color": None}
#     # print(foi)
#     # doi = readJSON("Cognitive Robotics\\Project\\tests\\Example Files\\results0.json", dict((k, foi[k]) for k in []))
#     # print(doi)
#     # x = count_item(doi, dict((k, foi[k]) for k in ['upper_color']))
#     # print(x)
    
#     entities = []
#     entities.append({"entity": "negation", 'value': "neither"})
#     entities.append({"entity": "gender", 'value': "female"})
#     # entities.append({"entity": "negation", 'value': "neither"})
#     entities.append({"entity": "hat", 'value': "visor"})
#     # entities.append({"entity": "negation", 'value': "nor"})
#     # entities.append({"entity": "bag", 'value': "rucksack"})
#     # entities.append({"entity": "negation", 'value': "nor"})
#     # entities.append({"entity": "color", 'value': "red"})
#     # entities.append({"entity": "top", 'value': "upper_cloth"})
#     entities.append({"entity": "negation", 'value': "nor"})
#     entities.append({"entity": "passages", 'value': "one hundred times"})
#     # entities.append({"entity": "time", 'value': "30 seconds"})
#     entities.append({"entity": "place", 'value': "supermarket"})
#     entities.append({"entity": "time", 'value': "one hundred seconds"})
#     cp = CountPeople()
    
#     flag = cp.update(entities)
    
#     if flag is False:
#         print("ERROR!")
    
#     print(cp.foi)

#     doi = cp.filteringJSON("Project\\tests\\results0.json")
#     print(doi)      
            
#     print(cp)
    
#     # [{'id': 3, 'gender': 'male', 'bag': True, 'hat': True, 'upper_color': 'blue', 'lower_color': 'black', 'roi1_passages': 2, 'roi1_persistence_time': 45, 'roi2_passages': 0, 'roi2_persistence_time': 0}, 
#     #  {'id': 9, 'gender': 'male', 'bag': False, 'hat': True, 'upper_color': 'white', 'lower_color': 'orange', 'roi1_passages': 0, 'roi1_persistence_time': 0, 'roi2_passages': 1, 'roi2_persistence_time': 18}]