from typing import NamedTuple
import requests


class Coordinates(NamedTuple):
    lat: float
    lon: float


HEADERS = {
    "User-Agent": "(Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Safari/537.36"
}
PLACES = {
    "Trondheim": Coordinates(lat=63.43, lon=10.39),
    "Oslo": Coordinates(lat=59.91, lon=10.75),
    "Bergen": Coordinates(lat=60.39, lon=5.32),
    "Avaldsnes": Coordinates(lat=59.35, lon=5.27),
    "Tromsø": Coordinates(lat=69.64, lon=18.95),
}


def get_air_temp_by_coordinates(lat: float, lon: float) -> float:
    url = (
        "https://api.met.no/weatherapi/locationforecast/2.0/compact?lat="
        f"{lat}&lon={lon}"
    )
    response = requests.get(url, headers=HEADERS, timeout=10)
    return response.json()["properties"]["timeseries"][0]["data"]["instant"][
        "details"
    ]["air_temperature"]


def get_air_temp_by_place(place: str) -> float:
    return get_air_temp_by_coordinates(*PLACES[place])


def main():
    for key in PLACES:
        print(get_air_temp_by_place(key))


if __name__ == "__main__":
    main()
