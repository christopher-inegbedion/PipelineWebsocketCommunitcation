import asyncio
from asyncio.tasks import sleep
import websockets
import uuid
import json
import threading


socket = None


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


pipeline = Pipeline("pipe")


def main():
    while True:
        action = input("command: ")

        if action == "exit":
            return False
        else:
            parse_action(action)


def parse_action(command):
    global pipeline

    if command == "init":
        asyncio.get_event_loop().run_until_complete(init())
    elif command == "rec":
        asyncio.get_event_loop().run_until_complete(recv())
    elif command == "msg":
        message = input("enter message here: ")
        asyncio.get_event_loop().run_until_complete(msg(message))
    elif command == "monitor":
        name = input("pipeline name: ")
        asyncio.run(monitor(name))
    elif command == "create":
        name = input("pipeline name: ")
        asyncio.get_event_loop().run_until_complete(create(name))
    else:
        print("unknown")


async def init():
    global socket
    addr = "ws://localhost:8000"
    socket = await websockets.connect(addr)


async def create(name):
    addr = "ws://localhost:8000/create"
    socket = await websockets.connect(addr)
    await socket.send(name)

    print(f"> {await socket.recv()}")


async def recv():
    global socket
    addr = "ws://localhost:8000/r"
    socket = await websockets.connect(addr)

    while socket.open:
        print(f"> {await socket.recv()}")


async def msg(message):
    addr = "ws://localhost:8000/msg"
    socket = await websockets.connect(addr)

    await socket.send(message)


async def monitor(name):
    global socket
    addr = "ws://localhost:8000/monitor"

    socket = await websockets.connect(addr)
    await socket.send(name)

    if await socket.recv() == "fail":
        print(f"{name} cannot be found")
        return False

    initial_response = json.loads(await socket.recv())

    if initial_response["response"] == "success":
        print("monitoring...")
        while socket.open:
            await asyncio.sleep(0.1)
            print(f"> {await socket.recv()}")
    else:
        print("fail")
        return False

main()
