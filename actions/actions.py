from typing import Any, Text, Dict, List, Optional

from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

import logging
from .CustomerTrackingSystem import CustomerTrackingSystem

FILE_PATH = "tests\\results0.json"
ROI_1 = "supermarket"
ROI_2 = "bar"

logging.getLogger(__name__)

# ====================================================
#  Class: ActionCountPeople(Action)
# ====================================================
class ActionCountPeople(Action):
    """
    Custom action for counting and providing information about people based on specified criteria.

    This action is designed to count and provide information about people passing through designated regions (ROIs)
    in a customer tracking system. It utilizes the CustomerTrackingSystem class for data processing.

    Global Attributes:
    - FILE_PATH (str): The file path to the JSON data containing information about people.
    - ROI_1 (str): The identifier for the first Region of Interest (ROI).
    - ROI_2 (str): The identifier for the second Region of Interest (ROI).

    Methods:
    - name(self) -> Text: Returns the name of the action ("action_count_people").
    - run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    Executes the action, counts people based on specified criteria, and provides relevant information.
    """
    
    def name(self) -> Text:
        """
        Returns the name of the action.

        Returns:
        - Text: The name of the action ("action_count_people").
        """
        return "action_count_people"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Executes the action, counts and provides the number of people who fulfil certain criteria set by the user.

        Parameters:
        - dispatcher (CollectingDispatcher): The dispatcher to send messages to the user.
        - tracker (Tracker): The conversation tracker containing user input history.
        - domain (Dict[Text, Any]): The domain configuration for the assistant.

        """

        # Extract current entities from the tracker
        entities = tracker.latest_message.get('entities')
        current_slots = tracker.current_slot_values()

        # Initialize the CustomerTrackingSystem
        cp = CustomerTrackingSystem(FILE_PATH, ROI_1, ROI_2, dispatcher, entities)
        for key, value in current_slots.items():
            if key in cp.foi:
                if value is not None and isinstance(value, list):
                    cp.foi[key] = tuple(value)
                else: 
                    cp.foi[key] = value if value != "None" else None

        print("=== ACTION COUNT PEOPLE ===")

        # Update the field of interest
        if cp.update() is True:
            print(cp.foi)
            # Get the data of interest - that is, the list of people that meet the required specifications.
            doi = cp.filteringJSON()

            print(doi)      
            
            dispatcher.utter_message(text=str(cp))
        
        print(cp.foi)
        
        return [
            SlotSet(key, value) 
            for key, value in cp.foi.items()
        ]

# ====================================================
#  Class: ActionReset(Action)
# ====================================================
class ActionReset(Action):

    def name(self) -> Text:
        return "action_reset"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            # Reset all slots
            print("=== ACTION RESET ===")
            return [AllSlotsReset()]

# ====================================================
#  Class: ActionsSlotMapping(Action)
# ====================================================
class ActionSlotMapping(Action):
    '''
    Custom action for mapping and updating slots based on recognized entities.
    '''

    def name(self) -> Text:
        """
        Returns the name of the action.

        Returns:
        - Text: The name of the action ("action_slot_mapping").
        """
        return "action_slot_mapping"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        Executes the action, maps and updates slots based on recognized entities.

        Parameters:
        - dispatcher (CollectingDispatcher): The dispatcher to send messages to the user.
        - tracker (Tracker): The conversation tracker containing user input history.
        - domain (Dict[Text, Any]): The domain configuration for the assistant.

        Returns:
        - List[Dict[Text, Any]]: The list of events to be processed by the dialogue engine.
        """
        print("=== ACTION SLOT MAPPING ===")
        
        current_group: Dict[Text, Any] = dict()

        # Reset Slots if intent is 'finding_someone'
        if tracker.get_intent_of_latest_message() == 'finding_someone':
            new_slot_values = {key: None for key in tracker.current_slot_values().keys()}      
        else:
            new_slot_values = {key: value for key, value in tracker.current_slot_values().items()}      

        # Extract Entities
        entities = tracker.latest_message.get('entities')
        
        for entity in entities:
            print(f"Entity: {entity['entity']}, Value: {entity['value']}")

            entity_key = entity['entity']
            entity_value = entity['value']

            current_group[entity_key] = entity_value
                        
            # Update Clothing Fields
            if "clothing" in entity_key:
                neg = "negation" in current_group
                color = current_group.get("color", None)
                
                current_group.clear()

                if color and entity_value in ["top", "trouser"]:
                    cloth = "upper_color" if entity_value == "top" else "lower_color"
                    if not neg:
                        new_slot_values[cloth] = color
                    else:
                        dispatcher.utter_message(text=f"Could you explain better? It would be easier if you provide me the color of the {entity_value}.")
                elif not color and entity_value in ["hat", "bag"]:
                    new_slot_values[entity_value] = not neg
                else:
                    dispatcher.utter_message(text=f"Could you explain better? Remember, I am not able to recognize the colors of hats and bags, only of shirts and pants.")
            if "gender" in entity_key:
                neg = not "negation" in current_group
                current_group.clear()
                new_slot_values["gender"] = entity_value if neg is True else "female" if entity_value == "male" and neg is False else "male"
        
        return [
            SlotSet(key, value) 
            for key, value in new_slot_values.items()
        ]

# ====================================================
#  Class: ActionSubmit(Action)
# ====================================================
class ActionSubmit(Action):

    def name(self) -> Text:
        return "action_submit"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            # Initialize the CustomerTrackingSystem
            cp = CustomerTrackingSystem(FILE_PATH, ROI_1, ROI_2, dispatcher)
            
            # Extract current slot values from the tracker and update corresponding fields in CustomerTrackingSystem
            current_slots = tracker.current_slot_values()
            for key, value in current_slots.items():
                if key in cp.foi:
                    print(f'{value} - Tipo: {type(value)}')
                    cp.foi[key] = value if value != "None" else None
            
            # Filter JSON data based on the specified criteria (fields of interest)
            doi = cp.filteringJSON()
            
            # Check if there are filtered people
            if cp.nop != 0:
                # Iterate through filtered people and construct output string
                for i, field in enumerate(doi):
                    if cp.nop == 1:
                        gender_string = "He " if field["gender"] == "male" else "She " 
                    elif cp.nop > 1:
                        gender_string = "The person n.{i} "
                    else: 
                        dispatcher.utter_message("I encountered problems. Can you formulate your question better?")
                        return[AllSlotsReset()]
                    # Convert ROI passages to string format
                    roi1_passages_string = "once" if field["roi1_passages"] == 1 else "twice" if field["roi1_passages"] == 2 else f'{field["roi1_passages"]} times'
                    roi2_passages_string = "once" if field["roi2_passages"] == 1 else "twice" if field["roi2_passages"] == 2 else f'{field["roi2_passages"]} times'
                    # Construct the final output string
                    output_string = gender_string + f"passed in front of the supermarket {roi1_passages_string} and {roi2_passages_string} in front of the bar."
                # Send the constructed message to the user
                dispatcher.utter_message(str(cp) + " " + output_string)
            else:
                # If no people are found, send an appropriate message to the user
                dispatcher.utter_message("I'm sorry. " + str(cp) + " I can assist you by calling the mall security. They will be here in a few seconds.")
            
            # Reset all slots after processing
            return [AllSlotsReset()]
        
# ====================================================
#  Class: ValidateFindPersonForm(FormValidationAction) 
# ====================================================
class ValidateFindPersonForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_find_person_form"

    def validate_gender(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        if tracker.get_intent_of_latest_message() != "doubt" and slot_value is not None:
            if slot_value.lower() in ['male', 'm']:
                return {"gender": "male"}
            elif slot_value.lower() in ['female', 'f']:
                return {"gender": "female"}
            else:
                dispatcher.utter_message("Please provide a valid gender (male/female).")
                return {"gender": None}
        elif tracker.get_intent_of_latest_message() == "doubt":
            dispatcher.utter_message(text="It would help me a lot if you would tell me the gender.")
            return {"gender": None} 
        else:
            return {"gender": None}
        
    def validate_upper_color(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        if slot_value is not None:
            if slot_value and tracker.get_intent_of_latest_message() != "doubt":
                return {"upper_color": slot_value}
            elif tracker.get_intent_of_latest_message() == "doubt":
                dispatcher.utter_message(response="utter_doubt")
                return {"upper_color": "None"} 
            elif slot_value is None:
                dispatcher.utter_message("Please provide a valid lower color.")
                return {"upper_color": None}
        return {"upper_color": None}

    def validate_lower_color(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        if slot_value is not None:
            if slot_value and tracker.get_intent_of_latest_message() != "doubt":
                return {"lower_color": slot_value}
            elif tracker.get_intent_of_latest_message() == "doubt":
                dispatcher.utter_message(response="utter_doubt")
                return {"lower_color": "None"} 
            elif slot_value is None:
                dispatcher.utter_message("Please provide a valid lower color.")
                return {"lower_color": None}
        else:
            return {"lower_color": None}
        
    def validate_bag(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:        

        if slot_value is not None:
            if slot_value is not None and isinstance(slot_value, bool):
                return {"bag": True if slot_value is True else False}
            elif tracker.get_intent_of_latest_message() == "doubt":
                return {"bag": "None"} 
            else:
                dispatcher.utter_message("Please provide a valid response (yes/no).")
                return {"bag": None}
        else:
            return {"bag": None}

    def validate_hat(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        if slot_value is not None:
            if slot_value is not None and isinstance(slot_value, bool):
                return {"hat": True if slot_value is True else False}
            elif tracker.get_intent_of_latest_message() == "doubt":
                dispatcher.utter_message(response="utter_doubt")
                return {"hat": "None"} 
            else:
                dispatcher.utter_message("Please provide a valid response (yes/no).")
                return {"hat": None}
        else:
            return {"hat": None}