from typing import Any, Text, Dict, List, Optional

from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

from .CustomerTrackingSystem import CustomerTrackingSystem

FILE_PATH = "tests\\results0.json"
ROI_1 = "supermarket"
ROI_2 = "bar"

# ====================================================
#  Class: ActionCountPeople(Action)
# ====================================================
class ActionCountPeople(Action):

    def name(self) -> Text:
        return "action_count_people"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        ) -> List[Dict[Text, Any]]:
                
        # Extract current entities from the tracker
        entities = tracker.latest_message.get('entities')

        # Initialize the CustomerTrackingSystem
        cp = CustomerTrackingSystem(FILE_PATH, ROI_1, ROI_2, dispatcher, entities)

        print("=== ACTION COUNT PEOPLE ===")

        # Update the field of interest
        if cp.update() is True:
            print(cp.foi)
            # Get the data of interest - that is, the list of people that meet the required specifications.
            doi = cp.filteringJSON()

            print(doi)      
            
            dispatcher.utter_message(text=str(cp))
        
        return []

# ====================================================
#  Class: GlobalSlotMapping(Action)
# ====================================================
class GlobalSlotMapping(Action):
    '''

    Args:
        Action (_type_): _description_
    '''

    def name(self) -> Text:
        return "global_slot_mapping"

    def run(self, 
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:

        print("=== GLOBAL SLOT MAPPING ===")
        print(tracker.latest_message.get("intent"))

        new_slot_values: Dict[Text, Any] = dict()
        current_group: Dict[Text, Any] = dict()
                
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

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]
        ) -> List[Dict[Text, Any]]:
            # Initialize the CustomerTrackingSystem
            cp = CustomerTrackingSystem(FILE_PATH, ROI_1, ROI_2, dispatcher)
            
            # Extract current slot values from the tracker and update corresponding fields in CustomerTrackingSystem
            current_slots = tracker.current_slot_values()
            for key, value in current_slots.items():
                if key in cp.foi:
                    cp.foi[key] = value if value != "None" else None
            
            # Filter JSON data based on the specified criteria (fields of interest)
            doi = cp.filteringJSON()
            
            # Check if there are filtered people
            if cp.nop != 0:
                # Iterate through filtered people and construct output string
                for i, field in enumerate(doi):
                    if cp.nop == 1:
                        gender_string = "He " if field["gender"] == "male" else "She " 
                    else:
                        gender_string = "The person n.{i} "
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
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(value)
        if value.lower() in ['male', 'm']:
            return {"gender": "male"}
        elif value.lower() in ['female', 'f']:
            return {"gender": "female"}
        else:
            dispatcher.utter_message("Please provide a valid gender (male/female).")
            return {"gender": None}

    def validate_upper_color(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        intent = tracker.latest_message['intent'].get('name')
        if slot_value and intent != "doubt":
            return {"upper_color": slot_value}
        elif intent == "doubt":
            dispatcher.utter_message(response="utter_doubt_intent")
            return {"upper_color": "None"} 
        elif slot_value is None:
            dispatcher.utter_message("Please provide a valid lower color.")
            return {"upper_color": None}

    def validate_lower_color(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        intent = tracker.latest_message['intent'].get('name')
        if slot_value and intent != "doubt":
            return {"lower_color": slot_value}
        elif intent == "doubt":
            dispatcher.utter_message(response="utter_doubt_intent")
            return {"lower_color": "None"} 
        elif slot_value is None:
            dispatcher.utter_message("Please provide a valid lower color.")
            return {"lower_color": None}

    def validate_bag(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:        
        intent = tracker.latest_message['intent'].get('name')
        if slot_value is not None and isinstance(slot_value, bool):
            return {"bag": True if slot_value is True else False}
        elif intent == "doubt":
            dispatcher.utter_message(response="utter_doubt_intent")
            return {"bag": "None"} 
        else:
            dispatcher.utter_message("Please provide a valid response (yes/no).")
            return {"bag": None}

    def validate_hat(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        intent = tracker.latest_message['intent'].get('name')
        if slot_value is not None and isinstance(slot_value, bool):
            return {"hat": True if slot_value is True else False}
        elif intent == "doubt":
            dispatcher.utter_message(response="utter_doubt_intent")
            return {"hat": "None"} 
        else:
            dispatcher.utter_message("Please provide a valid response (yes/no).")
            return {"hat": None}
        