from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Sequence
from typing import Any

import dearpygui.dearpygui as dpg


SEND_RECEIPT_READ = "read"
SEND_RECEIPT_DELIVERED = "delivered"

RECEIVE_STATUS_READ = "read"

PRIMARY_WINDOW = "main"
STATUS_LABEL = "status_label"
MY_NAME_LABEL = "my_name_label"
MESSAGE_INPUT = "message_input"
CONTACT_LIST = "contact_list"

MESSAGE_GROUP = "MESSAGE_GROUP"

COLOR_MESSAGE_ME = (0, 150, 255)
COLOR_MESSAGE_OTHERS = (255, 255, 255)

COLOR_ACCENT = (0, 150, 255)

MESSAGE_INDENT = 100

MAIN_WINDOW_WIDTH = 600
MAIN_WINDOW_HEIGHT = 500
CONTACT_LIST_WIDTH = 150
MESSAGE_INPUT_HEIGHT = 80
MESSAGE_WINDOW_HEIGHT = MAIN_WINDOW_HEIGHT - MESSAGE_INPUT_HEIGHT - 60


def get_team_prefix(label: str) -> str:
    return label.split("(")[0]


class Message:
    def __init__(
        self,
        sender: str,
        receiver: str,
        message: str,
        message_uuid: str,
        sent_by_me: bool,
    ) -> None:
        self.sender = sender
        self.message = message
        self.receiver = receiver
        self.uuid = message_uuid
        self.send_status = None
        self.receive_status = None
        self.sent_by_me = sent_by_me

    def as_string(self) -> str:
        if self.send_status is not None:
            return f"{self.sender}:\n  {self.message}\n ({self.send_status})"
        return self.sender + ":\n  " + self.message

    def set_send_status(self, send_status: str) -> None:
        self.send_status = send_status

    def is_sent_by_me(self) -> bool:
        return self.sent_by_me

    def is_read(self) -> bool:
        return self.receive_status == RECEIVE_STATUS_READ

    def mark_as_read(self) -> None:
        self.receive_status = RECEIVE_STATUS_READ

    @staticmethod
    def create_message(sender: str, receiver: str, message: str) -> Message:
        return Message(sender, receiver, message, uuid.uuid4().hex, True)


class History:
    def __init__(self, contact: str) -> None:
        self.contact = contact
        self.messages: list[Message] = []
        self.messages_by_uuid: dict[str, Message] = {}
        self.typing = False
        self.unread = 0

    def add_message(self, message: Message) -> None:
        self.messages.append(message)
        self.messages_by_uuid[message.uuid] = message
        self.unread = self.unread + 1

    def set_message_status(self, message_uuid: str, status: str) -> None:
        if message_uuid in self.messages_by_uuid:
            self.messages_by_uuid[message_uuid].set_send_status(status)

    def _get_rows(self) -> Sequence[Sequence[str]]:
        return [[message.as_string()] for message in self.messages]

    def set_typing(self, typing: bool) -> None:
        self.typing = typing

    def is_typing(self) -> bool:
        return self.typing

    def get_unread_messages(self) -> int:
        return self.unread

    def mark_as_read(self) -> Sequence[str]:
        receipts: list[str] = []
        for message in self.messages:
            if not (message.is_sent_by_me() or message.is_read()):
                receipts.append(message.uuid)
                message.mark_as_read()
        self.unread = 0
        return receipts

    def __str__(self) -> str:
        if self.unread:
            return f"{self.contact}({self.unread})"
        return self.contact


class Data:
    def __init__(self, contacts: Sequence[str], myself: str) -> None:
        if myself not in contacts:
            raise ValueError(
                f"The value for parameter 'myself' is {myself}, but it needs "
                f"to be one of the registered names {contacts}."
            )

        self.contacts = contacts
        self.histories: list[History] = []
        self.history_by_contact: dict[str, History] = {}
        self.myself = myself
        for contact in contacts:
            history = History(contact)
            self.history_by_contact[contact] = history
            self.histories.append(history)

    def get_history_by_contact(self, contact: str) -> History | None:
        if contact in self.history_by_contact:
            return self.history_by_contact[contact]
        return None


class ChatGui:
    def __init__(
        self,
        myself: str,
        on_send: Callable,
        on_type: Callable,
        on_read: Callable,
        typing_timeout_seconds: int = 3,
    ) -> None:
        contacts = (
            [f"team{i}a" for i in range(1, 13)]
            + [f"team{i}b" for i in range(1, 13)]
            + [f"x{i}" for i in range(1, 7)]
        )
        if myself not in contacts:
            raise ValueError(
                f"The value for parameter 'myself' is {myself}, but it needs "
                f"to be one of the registered names {contacts}."
            )
        contacts.remove(myself)
        self.data = Data(contacts, myself)
        self.changed = False
        self.last_update: float = time.time()
        self.typing_timestamps: dict[str, float | None] = {}
        self.on_send = on_send
        self.on_type = on_type
        self.on_read = on_read
        self.typing_timeout_seconds = typing_timeout_seconds

    def receive(self, sender: str, message: str, message_uuid: str) -> None:
        if history := self.data.get_history_by_contact(sender):
            history.add_message(
                Message(sender, self.data.myself, message, message_uuid, False)
            )
            self.changed = True

    def send(self, receiver: str, message_body: str) -> None:
        message = Message.create_message(
            self.data.myself, receiver, message_body
        )
        if history := self.data.get_history_by_contact(receiver):
            history.add_message(message)
            # forward to callback
            self.on_send(
                self.data.myself, receiver, message.message, message.uuid
            )

    def typing(self, sender: str) -> None:
        if history := self.data.get_history_by_contact(sender):
            history.set_typing(True)
            self.changed = True

    def receipt_read(self, sender: str, message_uuid: str) -> None:
        if history := self.data.get_history_by_contact(sender):
            history.set_message_status(message_uuid, SEND_RECEIPT_READ)
            self.changed = True

    def receipt_delivered(self, sender: str, message_uuid: str) -> None:
        if history := self.data.get_history_by_contact(sender):
            history.set_message_status(message_uuid, SEND_RECEIPT_DELIVERED)
            self.changed = True

    def call_list(self, sender: Any, data: Any) -> None:
        self.changed = True

    def call_send_button(
        self, sender: Any, app_data: Any, user_data: bool
    ) -> None:
        message: str = dpg.get_value(MESSAGE_INPUT)
        receiver: str = dpg.get_value(CONTACT_LIST)
        send_to_all = user_data
        self.typing_timestamps[receiver] = None
        dpg.set_value(MESSAGE_INPUT, "")
        if send_to_all:
            for receiver in self.data.contacts:
                self.send(receiver, message)
        else:
            self.send(receiver, message)
        self.changed = True

    def call_write(self, sender_widget: Any, data: Any) -> None:
        index = dpg.get_value(CONTACT_LIST)
        if (receiver := self.data.get_history_by_contact(index)) is None:
            return
        receiver = receiver.contact
        now = time.time()
        if receiver in self.typing_timestamps:
            last_timestamp = self.typing_timestamps[receiver]
            if (last_timestamp is not None) and (
                now - last_timestamp < self.typing_timeout_seconds
            ):
                return
        self.typing_timestamps[receiver] = now
        # call typing callback
        self.on_type(self.data.myself, receiver)

    def show_history_messages(self, history: History) -> None:
        dpg.delete_item(MESSAGE_GROUP, children_only=True)
        width = dpg.get_item_width(MESSAGE_GROUP)
        for message in history.messages:
            if not isinstance(width, int):
                continue
            if message.is_sent_by_me():
                dpg.add_text(
                    message.as_string(),
                    parent=MESSAGE_GROUP,
                    indent=MESSAGE_INDENT,
                    wrap=width - MESSAGE_INDENT,
                    color=COLOR_MESSAGE_OTHERS,
                )
            else:
                dpg.add_text(
                    message.as_string(),
                    parent=MESSAGE_GROUP,
                    indent=0,
                    wrap=width - MESSAGE_INDENT,
                    color=COLOR_MESSAGE_ME,
                )

    def update_table(self) -> None:
        contact = dpg.get_value(CONTACT_LIST)
        contact = get_team_prefix(contact)
        # history = dpg.get_value(CONTACT_LIST)
        if (history := self.data.get_history_by_contact(contact)) is None:
            return
        for message_uuid in history.mark_as_read():
            self.on_read(self.data.myself, history.contact, message_uuid)
        if history.is_typing():
            dpg.set_value(STATUS_LABEL, f"{history.contact} is typing...")
            history.set_typing(False)
        else:
            dpg.set_value(STATUS_LABEL, "")
        self.show_history_messages(history)

    def main_callback(self) -> None:
        if (self.last_update + 1 < time.time()) or self.changed:
            self.changed = False
            self.last_update = time.time()
            self.update_table()
            # dpg.set_value(CONTACT_LIST, self.data.histories)

    def _show_gui(self) -> None:
        with dpg.window(
            tag=PRIMARY_WINDOW,
            width=MAIN_WINDOW_WIDTH,
            height=MAIN_WINDOW_HEIGHT,
        ):
            with dpg.group(horizontal=True):
                with dpg.child_window(
                    width=CONTACT_LIST_WIDTH, height=MAIN_WINDOW_HEIGHT
                ):
                    dpg.add_listbox(
                        tag=CONTACT_LIST,
                        items=[
                            str(history) for history in self.data.histories
                        ],
                        width=-1,
                        num_items=len(self.data.contacts),
                        callback=self.call_list,
                    )
                with dpg.group(horizontal=False):
                    with dpg.group(width=-1, horizontal=True):
                        with dpg.child_window(
                            tag=MESSAGE_GROUP,
                            width=-1,
                            height=MESSAGE_WINDOW_HEIGHT,
                        ):
                            dpg.add_text("No message yet")

                    dpg.add_text(
                        tag=STATUS_LABEL, label="", color=COLOR_ACCENT
                    )
                    dpg.add_input_text(
                        default_value="",
                        multiline=True,
                        label="",
                        tag=MESSAGE_INPUT,
                        width=-1,
                        height=MESSAGE_INPUT_HEIGHT,
                        hint="Write...",
                        callback=self.call_write,
                    )
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Send",
                            width=100,
                            callback=self.call_send_button,
                            user_data=False,
                        )
                        dpg.add_button(
                            label="Send To All",
                            width=100,
                            callback=self.call_send_button,
                            user_data=True,  # send all
                        )

    def show(self) -> None:
        dpg.create_context()
        dpg.create_viewport(
            title="MQTT Message Chat (me: " + self.data.myself + ")",
            width=MAIN_WINDOW_WIDTH,
            height=MAIN_WINDOW_HEIGHT,
        )
        dpg.setup_dearpygui()
        self._show_gui()
        dpg.show_viewport()
        dpg.set_primary_window(PRIMARY_WINDOW, True)
        while dpg.is_dearpygui_running():
            self.main_callback()
            dpg.render_dearpygui_frame()
        dpg.destroy_context()
