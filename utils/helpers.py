import hashlib

def encrypt(data):
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def interpret_input_value(value):
    value = str(value).lower().strip()
    if value == "all":
        return "all"

    if value.endswith("k"):
        return int(float(value[:-1]) * 1000)

    return int(value)