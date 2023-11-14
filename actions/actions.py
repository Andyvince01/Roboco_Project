from typing import Any, Text, Dict, List

from rasa_sdk.events import SlotSet
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


location_db = {
    'Zara':"You shoud be able to find Zara just around the corner",
    'OVS':"You have to go upstairs",
    'Primark': "It's right behind you!",
    'H&M': "You have to go downstairs",
    'Sephora': "A few meter towards this direction!"
}

class ActionSayStoreLocation(Action):


    def name(self) -> Text:
        return "action_say_store_location"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        store_name = tracker.get_slot("store_name")
        info = location_db.get(store_name, None)
        if(info!=None):
            dispatcher.utter_message(text=info)
        else:
            dispatcher.utter_message(text="Actually, I don't think this store is in our Shopping Mall, I'm Sorry!")

        return []

class ActionCheckDiscountStore(Action):

    def name(self) -> Text:
        return "action_check_discount_store"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dictStore = readStoreDiscount("C:\\Users\\Andrea\\Desktop\\Progetto\\actions\\discountStore.txt")

        store = tracker.get_slot("store_name").lower() # per permettere il confronto sempre con gli store scritti nel file

        if store in dictStore:
            if dictStore[store] == "true":
                dispatcher.utter_message(text=f"There are several discounts available for {store}!")
            else:
                dispatcher.utter_message(text=f"Sorry, there is no discount for {store}.")
        else:
            dispatcher.utter_message(text=f"I don't have information for {store}.")

        return []

def readStoreDiscount(nome_file):
        # apre il file in modalità lettura
        file = open(nome_file, "r")

        file.readline() # saltiamo la prima riga

        # crea un dizionario vuoto
        dizionario = {}
        # legge ogni riga del file
        for riga in file:
            # rimuove il carattere di fine riga
            riga = riga.strip()
            # suddivide la riga in due parti usando il ";" come separatore
            store, discount = riga.split(";")
            # aggiunge al dizionario una chiave con il nome del negozio e un valore booleano del discount
            dizionario[store] = discount
        # chiude il file
        file.close()
        # ritorna il dizionario
        return dizionario
