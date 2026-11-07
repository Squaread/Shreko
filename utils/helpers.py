import hashlib
import unicodedata

def encrypt(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def interpret_input_value(value):
    value = str(value).lower().strip()
    if value == "all":
        return "all"

    if value.endswith("k"):
        return int(float(value[:-1]) * 1000)

    return int(value)

def count_vowels(text: str):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower()
    vowels = "aeiou"
    total_text_vowels = sum(1 for letter in text if letter in vowels)
    return total_text_vowels

def count_consonants(text: str):
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8').lower()
    vowels = "aeiou"    
    total_text_consonants = sum(1 for letter in text if letter.isalpha() and letter not in vowels)
    return total_text_consonants