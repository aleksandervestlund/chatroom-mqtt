from typing import Any
from chat_gui import ChatGui


def on_send(sender: str, receiver: str, message: str, uuid: Any) -> None:
    print(f"Sending {sender} --> {receiver} {message[:5]}...")


def on_type(sender: str, receiver: str) -> None:
    print(f"Typing: {sender} --> {receiver}")


def on_read(sender: str, receiver: str, uuid: str) -> None:
    print(f"Read: {sender} --> {receiver} {uuid[:5]}...")


def main() -> None:
    my_id = "team5b"
    gui = ChatGui(my_id, on_send=on_send, on_type=on_type, on_read=on_read)

    # We send in a fake message:
    gui.receive("x6", "Dette er en fake medling!", "absgdeff")

    # We fake that chat partner x5 starts typing:
    gui.typing("x5")

    gui.show()


if __name__ == "__main__":
    main()
