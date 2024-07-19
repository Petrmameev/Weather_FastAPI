import json


def get_coords_by_name(name_city):
    with open("russian-cities.json", "r", encoding="utf-8") as file:
        all_city = json.load(file)

    for city in all_city:
        if city["name"] == name_city:
            coord_lat = city["coords"]["lat"]
            coord_lon = city["coords"]["lon"]
            return coord_lat, coord_lon

    return None, None
