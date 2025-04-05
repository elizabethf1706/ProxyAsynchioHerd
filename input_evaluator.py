import re

def handle_errors(invalid_command):
    return f"? {invalid_command}"

def is_valid_upper_bound(upper_bound):
    try:
        upper_bound = int(upper_bound)
    except ValueError:
        return False
    return 0 <= upper_bound <= 20

def is_valid_radius(radius):
    try:
        radius = int(radius)
    except ValueError:
        return False
    return 0 <= radius <= 50

def is_valid_client_id(client_id):
    return bool(client_id) and not any(c.isspace() for c in client_id)

def is_valid_posix_time(timestamp):
    try:
        return float(timestamp) >= 0
    except ValueError:
        return False

def is_valid_location(location):
    pattern = r"^[+-](90(\.0+)?|[0-8]?\d(\.\d+)?)[+-](180(\.0+)?|1[0-7]\d(\.\d+)?|[0-9]?\d(\.\d+)?)$"
    return bool(re.fullmatch(pattern, location))

def is_valid_iamat(message):
    message = message.strip()
    pattern = r"^IAMAT\s+(\S+)\s+([+-]\d+(\.\d+)?[+-]\d+(\.\d+)?)\s+(\d+(\.\d+)?)$"
    match = re.fullmatch(pattern, message)
    if not match:
        return False
    parts = message.split()
    if len(parts) != 4:
        return False
    client_id, location, posix_time = parts[1], parts[2], parts[3]
    return (
        is_valid_client_id(client_id) and
        is_valid_location(location) and
        is_valid_posix_time(posix_time)
    )

def is_valid_whatsat(message):
    message = message.strip()
    pattern = r"^WHATSAT\s+(\S+)\s+(\d+)\s+(\d+)\s*$"
    match = re.fullmatch(pattern, message)
    if not match:
        return False
    parts = message.split()
    if parts[0] != "WHATSAT":
        return False
    client_id, radius, upper_bound = parts[1], parts[2], parts[3]
    return (
        is_valid_client_id(client_id) and
        is_valid_upper_bound(upper_bound) and
        is_valid_radius(radius)
    )
