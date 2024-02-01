import asyncio
import websockets
import time, json

connected = set()

async def server(websocket, path):
    # Register.
    connected.add(websocket)
    try:
        while True:
            for conn in connected:
                await conn.send()
            time.sleep(5)
    finally:
        # Unregister.
        connected.remove(websocket)

start_server = websockets.serve(server, "localhost", 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
