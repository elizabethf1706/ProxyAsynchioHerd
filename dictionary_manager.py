import asyncio

client_data = {}
data_lock = asyncio.Lock()

async def store_client_data(client_id, location, timestamp, server_name, rcvd_time):
    """
    Store client data if the new timestamp is more recent than the current record.
    
    Parameters:
      client_id (str): The client's identifier.
      location (str): The client's location (in ISO 6709 format).
      timestamp (str): The client's reported time (as a string representation of a float).
      server_name (str): The name of the server processing the update.
      rcvd_time (str): The server's time when the message was received.
    
    Returns:
      bool: True if the record was updated (new record or fresher update), otherwise False.
    """
    async with data_lock:
        # If there's already data for this client, compare timestamps.
        if client_id in client_data:
            stored_timestamp = float(client_data[client_id]['timestamp'])
            new_timestamp = float(timestamp)
            if new_timestamp <= stored_timestamp:
                # Do not update if the new data is not fresher.
                return False
        # Save or update the client's record.
        client_data[client_id] = {
            "location": location,
            "timestamp": timestamp,
            "server": server_name,
            "rcvd_time": rcvd_time
        }
        return True

async def get_client_data(client_id):
    async with data_lock:
        return client_data.get(client_id, None)
