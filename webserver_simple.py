import json
import socket
from urllib.parse import quote, unquote

import requests

from webserver import RequestHandler


def extract_json_string(string: str) -> str:
    start = string.find("{")
    stop = string.rfind("}")
    return string[start : stop + 1]


def get_ip_address() -> str:
    return socket.gethostbyname("localhost")


def dictionary_to_string(dictionary: dict) -> str:
    return json.dumps(dictionary)


def json_string_to_dictionary(json_string: str) -> dict:
    return json.loads(json_string)


def encode_string_into_url(string: str) -> str:
    return quote(string)


def decode_url_back_to_string(url_encoded_string: str) -> str:
    return unquote(url_encoded_string)


def string_to_unicode_bytes(string: str) -> bytes:
    return string.encode("utf-8")


def print_response(response: requests.Response) -> None:
    print("-------- Response --------")
    print(f"Status code: {response.status_code}")
    print("-------- Content--------")
    print(response.text)
    print("------------------------")


def do_POST(self: RequestHandler) -> None:
    """HTTP POST request as it comes from the sensor device application, for
    instance to send the current temerature.
    """

    print("-------- Incoming POST request --------")
    print(f"  Request data: {self.requestline}")

    decoded_request = decode_url_back_to_string(self.requestline)
    print(f"  Decoded data: {decoded_request}")

    json_string = extract_json_string(decoded_request)
    print(f"  Extracted JSON string: {json_string}")

    dictionary = json_string_to_dictionary(json_string)
    print(dictionary)

    temperature = dictionary["temperature"]
    print(f"Temperature {temperature} received in do_POST()")
    self.store_data("temperature", temperature)

    response = "ok"

    response_in_bytes = string_to_unicode_bytes(response)
    self.send_response(200)
    self.send_header("Content-type", "text/plain")
    self.end_headers()
    self.wfile.write(response_in_bytes)


def main() -> None:
    dictionary = {"temperature": 20.0, "sensor_name": "kitchen"}

    port = 8000
    response = requests.post(
        f"http://{get_ip_address()}:{port}/?data={dictionary}", timeout=10
    )
    print_response(response)


if __name__ == "__main__":
    main()
