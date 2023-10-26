from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import quote, unquote
import json
import socket


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


class RequestHandler(BaseHTTPRequestHandler):
    def store_data(self, name: str, data: str) -> None:
        setattr(
            self.server,
            "data",
            getattr(self.server, "data", {}) | {name: data},
        )

    def load_data(self, name: str) -> str | None:
        return getattr(self.server, "data", {}).get(name, None)

    def do_GET(self) -> None:
        # Phase 1: What has been requested?
        print("-------- Incoming GET request --------")
        print(f"  Request data: {self.requestline}")

        # Phase 2: Which data do we want to send back?
        response = "Hei hei"

        # Phase 3: Let's send back the data!
        response_in_bytes = string_to_unicode_bytes(response)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(response_in_bytes)

    def do_POST(self):
        """HTTP POST request as it comes from the sensor device application,
        for instance to send the current temerature."""

        print("-------- Incoming POST request --------")
        print(f"  Request data: {self.requestline}")

        decoded_request = decode_url_back_to_string(self.requestline)
        print(f"  Decoded data: {decoded_request}")

        json_string = extract_json_string(decoded_request)
        print(f"  Extracted JSON string: {json_string}")

        dictionary = json_string_to_dictionary(json_string)
        print(dictionary)

        # We extract the temperature...
        temperature = dictionary["temperature"]
        print(f"Temperature {temperature} received in do_POST()")
        # ...and store it
        # self.store_data("temperature", temperature)

        response = "ok"

        response_in_bytes = string_to_unicode_bytes(response)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(response_in_bytes)


def main() -> None:
    port = 8000
    httpd = HTTPServer(
        ("", port),
        RequestHandler,
    )
    print(
        "\n******** TTM4175 Web Server  ********\n"
        f"    The server will be reachable via  http://{get_ip_address()}:{port}/\n"
        "    Terminate the server via Ctrl-C.\n"
        "*************************************\n"
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
