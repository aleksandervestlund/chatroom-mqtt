import json
from typing import Any
import paho.mqtt.client as mqtt
from chat_gui import ChatGui


# Called by MQTT client when we are connected
def on_connect(mqttc: Any, obj: Any, flags: Any, rc: Any) -> None:
    print(f"Connected: {rc}")


# Called by the MQTT client for every message we receive
def on_message(mqttc: mqtt.Client, obj: Any, msg: Any) -> None:
    print(f"{msg.topic} {msg.qos} {msg.payload}")

    try:
        data = json.loads(msg.payload)
    except json.JSONDecodeError as e:
        print("The payload is not valid json!")
        print(e)
        return

    print(msg.topic)
    if msg.topic.endswith("message"):
        GUI.receive(data["sender"], data["message"], data["uuid"])
        # sending the delivery receipt, we switch sender and receiver
        receiver = data["sender"]
        sender = data["receiver"]
        payload_dict = {
            "sender": sender,
            "receiver": receiver,
            "uuid": data["uuid"],
        }
        payload_json = json.dumps(payload_dict)
        mqttc.publish(
            f"ttm4175/chat/{receiver}/delivered", payload=payload_json
        )
    elif msg.topic.endswith("delivered"):
        GUI.receipt_delivered(data["sender"], data["uuid"])
    elif msg.topic.endswith("read"):
        GUI.receipt_read(data["sender"], data["uuid"])
    elif msg.topic.endswith("typing"):
        GUI.typing(data["sender"])
    else:
        print(f"Unknown topic: {msg.topic}")


# Called by the Chat UI when we want to send a message
def on_send(sender: str, receiver: str, message: str, uuid: str) -> None:
    print(f"Sending {sender} --> {receiver} {message[:5]}...")
    payload_dict = {
        "sender": sender,
        "receiver": receiver,
        "message": message,
        "uuid": uuid,
    }
    payload_json = json.dumps(payload_dict)
    MQTTC.publish(f"ttm4175/chat/{receiver}/message", payload=payload_json)


# Called by the Chat UI when we start typing to somebody
def on_type(sender: str, receiver: str) -> None:
    print(f"Typing: {sender} --> {receiver}")
    payload_dict = {
        "sender": sender,
        "receiver": receiver,
    }
    payload_json = json.dumps(payload_dict)
    MQTTC.publish(f"ttm4175/chat/{receiver}/typing", payload=payload_json)


# Called by the Chat UI when we have read a message
def on_read(sender: str, receiver: str, uuid: str) -> None:
    print(f"Read: {sender} --> {receiver} {uuid[:5]}...")
    payload_dict = {
        "sender": sender,
        "receiver": receiver,
        "uuid": uuid,
    }
    payload_json = json.dumps(payload_dict)
    MQTTC.publish(f"ttm4175/chat/{receiver}/read", payload=payload_json)


MY_ID = "team5b"
GUI = ChatGui(MY_ID, on_send=on_send, on_type=on_type, on_read=on_read)
MQTTC = mqtt.Client()


def main() -> None:
    MQTTC.on_message = on_message
    MQTTC.on_connect = on_connect
    MQTTC.connect("mqtt20.iik.ntnu.no", 1883)
    MQTTC.loop_start()
    MQTTC.subscribe(f"ttm4175/chat/{MY_ID}/+")

    GUI.show()


if __name__ == "__main__":
    main()
