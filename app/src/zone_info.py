import os


def get_next_terror_zone():

    with open(os.path.join("server/data", "next_zone.txt"), "r") as file:
        zone_parts_next = file.read().splitlines()

    return zone_parts_next

def get_current_terror_zone():

    with open(os.path.join("server/data", "current_zone.txt"), "r") as file:
        zone_parts_current = file.read().splitlines()

    return zone_parts_current
