import asyncio
import websockets
import uuid
import json

change = False


class Pipeline:
    def __init__(self, name):
        self.name = name
        self.id = str(uuid.uuid4())
        self.status = "none"
        self.socket1 = None
        self.socket2 = None

    def start(self):
        self.status = "running"

    def stop(self):
        self.status = "stopped"


pipelines = {}
new_pipeline = Pipeline("pipe")
msg = ""


async def start(websocket, path):
    global new_pipeline, change, msg

    if path == "/r":
        while websocket.open:
            await asyncio.sleep(0.1)
            if change:
                await websocket.send("status changed")
                change = False
    elif path == "/msg":
        msg = await websocket.recv()
        change = True

        await websocket.send("sent")
    elif path == "/monitor":
        name = await websocket.recv()

        if name in pipelines:
            new_pipeline = pipelines[name]
            await websocket.send("success")
        else:
            await websocket.send("fail")

        if new_pipeline.socket1 == None:
            new_pipeline.socket1 = websocket

            await websocket.send(json.dumps({"response": "success"}))

            await websocket.send("[i] socket1 connected [i]")
            while new_pipeline.socket1.open:
                await asyncio.sleep(0.1)
                if change and new_pipeline.socket2 == None:
                    await new_pipeline.socket1.send(msg)
                    change = False
        elif new_pipeline.socket2 == None:
            new_pipeline.socket2 = websocket

            await websocket.send(json.dumps({"response": "success"}))

            await new_pipeline.socket1.send("[i] socket2 connected [i]")
            while websocket.open:
                await asyncio.sleep(0.1)
                if change:
                    await new_pipeline.socket1.send(msg)
                    await new_pipeline.socket2.send(msg)
                    change = False
    elif path == "/create":
        pipeline_name = await websocket.recv()
        pipeline = Pipeline(pipeline_name)
        pipelines[pipeline_name] = pipeline
        await websocket.send(f"Pipeline '{pipeline_name}' created with ID: {pipeline.id}")
    else:
        async for message in websocket:
            print(f"> message")
            change = True

            print(f"< {message} sent")
            await websocket.send(message + " sent")


start_server = websockets.serve(start, "localhost", 8000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
