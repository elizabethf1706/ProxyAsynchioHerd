
import re
import aiohttp
import asyncio
import json
from dictionary_manager import get_client_data

def time_calc(server_received_time, timestamp):
    try:
        client_timestamp = float(timestamp)
    except ValueError:
        return f"? {timestamp}"
    time_difference = server_received_time - client_timestamp
    return f"+{time_difference}" if time_difference >= 0 else f"{time_difference}"

def AT_response_toIAMAT(message, server_name, server_received_time):
    parts = message.split()
    client_id, location, timestamp = parts[1], parts[2], parts[3]
    t = time_calc(server_received_time, timestamp)
    response = f"AT {server_name} {t} {client_id} {location} {timestamp}"
    return response

async def AT_response_toWHATSAT(message, server_name, server_received_time):
    parts = message.split()
    client_id, radius, upper_bound = parts[1], parts[2], parts[3]
    client_info = await get_client_data(client_id)
    if client_info is None:
        return f"? {message}"
    location = client_info['location']
    timestamp = client_info['timestamp']
    orig_server = client_info['server']
    time_diff = time_calc(server_received_time, timestamp)
    match = re.match(r"([+-][\d.]+)([+-][\d.]+)", location)
    if not match:
        return f"? {message}"
    latitude, longitude = match.groups()
    coords = f"{latitude},{longitude}"
    radius_int = int(radius)
    upper_bound_int = int(upper_bound)
    response = f"AT {orig_server} {time_diff} {client_id} {location} {timestamp}"
    # Set a timeout of 10 seconds.
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        jdata = await get_places(session, coords, radius_int, upper_bound_int)
    return f"{response}\n{jdata}\n\n"
# https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=34.068930,-118.445127&radius=10&key=AIzaSyCqOH43EIiIlWck0pWvGN_MSG-CYqVAs0k

async def get_places(session, location, radius, upper_bound):
    API_KEY = "AIzaSyCqOH43EIiIlWck0pWvGN_MSG-CYqVAs0k"
    base_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&key={API_KEY}"

    try:
        async with session.get(base_url) as resp:
            if resp.status != 200:
                return json.dumps({"error": "API request failed"}, indent=2)
            data = await resp.json()
            if "results" in data:
                data["results"] = data["results"][:upper_bound]
            formatted = json.dumps(data, indent=2)
            formatted = "\n".join(line for line in formatted.splitlines() if line.strip() != "")
            return formatted
    except asyncio.TimeoutError:
        return json.dumps({"error": "Request timed out"}, indent=2)
    except aiohttp.ClientError as e:
        return json.dumps({"error": f"Network error: {str(e)}"}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {str(e)}"}, indent=2)
