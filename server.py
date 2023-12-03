import asyncio
import websockets
import json

port = 8001
connect_clients = set()

async def handler(websocket):
    connect_clients.add(websocket)
    
    while True:
        try:
            message = await websocket.recv()
            await asyncio.gather(*[client.send(message) for client in connect_clients])
        except websockets.ConnectionClosedOK:
            break
        except websockets.ConnectionClosedError:
            break
        except KeyboardInterrupt:
            break
        print(message)

async def main():
    async with websockets.serve(handler, "localhost", port):
        await asyncio.Future()

if __name__ == "__main__":
    print(f"Server iniciado em: http://localhost:{port}")
    asyncio.run(main())