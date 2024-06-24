import os


def get_terror_zone_info():

    with open(os.path.join("data", "next_zone.txt"), "r") as file:
        zone_parts_next = file.read().splitlines()

    return zone_parts_next
