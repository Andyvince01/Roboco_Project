from word2number import w2n

class Utils:
        
    @staticmethod
    def adverb_to_number(adverb, dispatcher):
        """
        Convert an adverb to a numerical value.

        Parameters:
        - adverb (str): An adverb indicating a frequency, e.g., "once", "twice", "3 times".

        Returns:
        - int or None: The numerical representation of the adverb if conversion is successful, or None if the conversion fails.

        Raises:
        - None

        Example:
        >>> obj = YourClassName()
        >>> obj.__adverb_to_number("once")
        1
        >>> obj.__adverb_to_number("twice")
        2
        >>> obj.__adverb_to_number("3 times")
        3
        >>> obj.__adverb_to_number("forty-one times")
        41
        >>> obj.__adverb_to_number("invalid adverb")
        None
        """
        if adverb == "once":
            return 1
        elif adverb == "twice":
            return 2
        elif adverb.endswith(" times"):
            try:
                number = adverb.split(" times")[0]
                return w2n.word_to_num(number)
            except ValueError:
                dispatcher.utter_message(text=f"My apologies! Please, provide a right frequency adverb in the format (once, twice, 'number' times). You provided me the following frequency adverb: " + adverb)
                return None
        else:
            return None
    
    
    @staticmethod
    def convert_time_to_seconds(time_string, dispatcher):
        """
        Convert a time string to seconds.

        Parameters:
        - time_string (str): A string representing a duration in natural language, e.g., "2 hours", "30 minutes", "15 seconds".

        Returns:
        - int or None: The equivalent duration in seconds if the conversion is successful, or None if the conversion fails.

        Raises:
        - None

        Example:
        >>> obj = YourClassName()
        >>> obj.convert_time_to_seconds("2 hours")
        7200
        >>> obj.convert_time_to_seconds("30 minutes")
        1800
        >>> obj.convert_time_to_seconds("twenty-one seconds")
        21
        >>> obj.convert_time_to_seconds("invalid input")
        None
        """
        amount_string = " ".join(time_string.split()[:-1])
        try:
            if "second" in time_string.split()[-1]:
                amount = w2n.word_to_num(amount_string)
            elif "minute" in time_string.split()[-1]:
                amount = w2n.word_to_num(amount_string) * 60
            elif "hour" in time_string.split()[-1]:
                amount = w2n.word_to_num(amount_string) * 3600        
            return amount
        except ValueError:
            dispatcher.utter_message(text=f"My apologies! Please, provide a right time_string in the format ('number' seconds, minutes, hours). You provided me the following time_string: " + time_string)
            return None

