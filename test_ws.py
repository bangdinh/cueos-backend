import asyncio
import websockets

async def test_websocket():
    print("Testing WebSocket connection...")
    try:
        async with websockets.connect("ws://127.0.0.1:8000/ws/admin") as ws:
            print("SUCCESS: Connected to backend WebSocket!")
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"RECEIVED: {msg[:100]}...")
            except asyncio.TimeoutError:
                print("TIMEOUT: No messages received in 5s.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
