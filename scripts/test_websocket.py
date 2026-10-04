import asyncio
import json

import websockets


async def test_methu():
    uri = "ws://127.0.0.1:8000/ws/methu"

    print("Connecting to METHU...")

    async with websockets.connect(uri) as websocket:

        # Initial connection event
        connected = await websocket.recv()
        connected_data = json.loads(connected)

        print("\nCONNECTED EVENT")
        print(json.dumps(connected_data, indent=2))

        # Send request
        request = {
            "message": "Methu, open Chrome and go to YouTube",
            "session_id": "multi-step-websocket-001",
        }

        print("\nSending request...")
        await websocket.send(json.dumps(request))

        # Thinking event
        thinking = await websocket.recv()
        thinking_data = json.loads(thinking)

        print("\nEVENT 1")
        print(json.dumps(thinking_data, indent=2))

        # Final UI event
        result = await websocket.recv()
        result_data = json.loads(result)

        print("\nEVENT 2")
        print("Event:", result_data.get("event"))
        print("Agent:", result_data.get("agent"))
        print("Status:", result_data.get("status"))
        print("Response:", result_data.get("response"))


asyncio.run(test_methu())
