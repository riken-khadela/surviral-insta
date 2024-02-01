import asyncio
import websockets

async def listen():
    uri = "ws://[Server IP or Hostname]:8765"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print(f"Received message: {message}")

asyncio.get_event_loop().run_until_complete(listen())
