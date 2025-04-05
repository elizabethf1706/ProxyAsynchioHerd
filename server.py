import asyncio
import time
import sys
from input_evaluator import is_valid_iamat, is_valid_whatsat, handle_errors
from input_returner import AT_response_toIAMAT, AT_response_toWHATSAT
from dictionary_manager import store_client_data  # Adjust to accept five parameters.

# Assigned ports for each server.
PORTS = {
    'Clark': 10003,
    'Campbell': 10002,
    'Bailey': 10000,
    'Bona': 10001,
    'Jaquez': 10004
}

# Mapping of neighbor servers.
SERVER_NEIGHBORS = {
    'Clark': ['Jaquez', 'Bona'],
    'Campbell': ['Bona', 'Bailey', 'Jaquez'],
    'Bona': ['Clark', 'Bailey', 'Campbell'],
    'Bailey': ['Bona', 'Campbell'],
    'Jaquez': ['Clark', 'Campbell']
}

async def flood_update(message):
    """Flood an UPDATE message to all neighbor servers."""
    for neighbor in SERVER_NEIGHBORS.get(server_name, []):
        neighbor_port = PORTS[neighbor]
        try:
            reader, writer = await asyncio.open_connection('127.0.0.1', neighbor_port)
            with open(f"{server_name}_log.txt", "a") as log_file:
                log_file.write(f"Flooding from {server_name} to {neighbor} on port {neighbor_port}: {message}\n")
            writer.write(message.encode() + b'\n')
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            with open(f"{server_name}_log.txt", "a") as log_file:
                log_file.write(f"Flooding from {server_name} to {neighbor} successful.\n")
        except Exception as e:
            with open(f"{server_name}_log.txt", "a") as log_file:
                log_file.write(f"Error flooding to {neighbor} on port {neighbor_port}: {e}\n")

async def handle_functions(message, server_name, server_received_time):
    # Handle IAMAT messages from clients.
    if is_valid_iamat(message):
        parts = message.strip().split()
        client_id, location, timestamp = parts[1], parts[2], parts[3]
        # Update client data.
        # Ensure store_client_data is modified to accept the server received time as a string.
        updated = await store_client_data(client_id, location, timestamp, server_name, str(server_received_time))
        # Compute time difference.
        time_diff = float(server_received_time) - float(timestamp)
        time_diff_str = f"+{time_diff}" if time_diff >= 0 else f"{time_diff}"
        response = f"AT {server_name} {time_diff_str} {client_id} {location} {timestamp}"
        # If this is a new update, flood the update.
        if updated:
            update_message = f"UPDATE {client_id} {server_name} {location} {timestamp} {server_received_time}"
            await flood_update(update_message)
        return response

    # Handle WHATSAT messages from clients.
    elif is_valid_whatsat(message):
        return await AT_response_toWHATSAT(message, server_name, server_received_time)

    # Handle UPDATE messages received from other servers.
    elif message.startswith("UPDATE"):
        parts = message.split()
        if len(parts) != 6:
            return handle_errors(message)
        # UPDATE message format: UPDATE <client_id> <origin_server> <location> <timestamp> <rcvd_time>
        client_id, origin_server, location, timestamp, rcvd_time = parts[1:]
        updated = await store_client_data(client_id, location, timestamp, origin_server, rcvd_time)
        if updated:
            await flood_update(message)
        # Do not send a response for UPDATE messages.
        return ""
    else:
        return handle_errors(message)

# A dictionary to track active client connections.
clients = {}

async def handle_client(reader, writer):
    info = writer.get_extra_info('peername')
    with open(f"{server_name}_log.txt", "a") as log_file:
        log_file.write(f"New connection from {info}\n")
    clients[writer] = info
    try:
        while True:
            data = await reader.readline()  # Wait for a full line.
            if not data:
                break  # Client disconnected.
            server_received_time = time.time()
            message = data.decode('utf-8').strip()
            with open(f"{server_name}_log.txt", "a") as log_file:
                log_file.write(f"[{info}] Received: {message} at {server_received_time}\n")
            response = await handle_functions(message, server_name, server_received_time)
            with open(f"{server_name}_log.txt", "a") as log_file:
                log_file.write(f"[{info}] Responded: {response}\n")
            # Only send a response if one is generated.
            if response:
                writer.write(response.encode() + b'\n')
                await writer.drain()
            if message.lower() == 'quit':
                break
    except asyncio.CancelledError:
        pass
    finally:
        with open(f"{server_name}_log.txt", "a") as log_file:
            log_file.write(f"Client {info} disconnected.\n")
        del clients[writer]
        writer.close()
        await writer.wait_closed()

async def main():
    global server_name
    if len(sys.argv) != 2:
        print("Usage: python3 server.py <ServerName>")
        exit(1)
    server_name = sys.argv[1].title()  # Convert provided name to title case.
    if server_name not in PORTS:
        print("Invalid server name. Valid names are:", ", ".join(PORTS.keys()))
        exit(1)
    port = PORTS[server_name]
    server = await asyncio.start_server(handle_client, '127.0.0.1', port)
    with open(f"{server_name}_log.txt", "a") as log_file:
        log_file.write(f"Server {server_name} started on 127.0.0.1:{port}\n")
    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            with open(f"{server_name}_log.txt", "a") as log_file:
                log_file.write(f"Server {server_name} shutting down...\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        with open(f"{server_name}_log.txt", "a") as log_file:
            log_file.write("Server manually stopped.\n")
