import re

pattern = r'(\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thir(?:teen|ty)|four(?:teen|ty)|fif(?:teen|ty)|six(?:teen|ty)|seven(?:teen|ty)|eight(?:een|y)|nine(?:teen|ty)|twenty|thirty(?:-[a-z]+)?|(?:one|two|three|four|five|six|seven|eight|nine) hundred(?: and [a-z]+)?)-?(?:one|two|three|four|five|six|seven|eight|nine))\b|\b\d+\b)\s*(second|minute|hour)s?'

text = "Il tempo necessario è di thirty-seven minutes o 25 secondi."

matches = re.findall(pattern, text)
for match in matches:
    print(match)
