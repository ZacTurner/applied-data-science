import sys
import csv
from datetime import datetime, timedelta
from itertools import chain
from pymongo import MongoClient
import numpy as np
import os

rooms = [
    "dining_room",
    "kitchen",
    "bathroom",
    "stairs",
    "bedroom",
    "hall",
    "living_room"
]


def cleansed_data():
    """Connect to the database and cleanse and filter the data"""

    client = MongoClient(
        os.environ["ADS_URL"],
        username=os.environ["ADS_USERNAME"],
        password=os.environ["ADS_PASSWORD"]
    )

    sensor_rooms = {
        "fd00::212:4b00:0:81": 0,
        "fd00::212:4b00:0:82": 1,
        "00144": 1,
        "fd00::212:4b00:0:86": 2,
        "fd00::212:4b00:0:87": 3,
        "fd00::212:4b00:0:84": 4,
        "fd00::212:4b00:0:83": 5,
        "fd00::212:4b00:0:80": 6
    }

    day = datetime(2018, 3, 21, 15)

    open_times = {
        6: day + timedelta(minutes=15),
        4: day + timedelta(minutes=17),
        1: day + timedelta(minutes=41),
        2: day + timedelta(hours=1, minutes=21)
    }

    close_time = datetime(2018, 3, 21, 16, 45)

    database = client.project
    collection = database.env_original

    outputs = []
    for doc in collection.find():
        if doc["uid"] in sensor_rooms:
            room = sensor_rooms[doc["uid"]]
            output = {}

            temps = []
            for val in doc["e"]:
                if val["n"] in ["BMP_TEMP", "HDC_TEMP"]:
                    temps.append(float(val["v"]))
                    output["temperature"] = np.mean(temps)
                elif val["n"] == "HDC_HUM":
                    output["humidity"] = float(val["v"])
                elif val["n"] == "ELEC":
                    if int(val["v"]) > 0:
                        output["kettle_power"] = int(val["v"])

            if output:
                output["time"] = doc["bt"]
                output["room"] = rooms[room]

                output["window_open"] = False
                output["window_open_time"] = 0

                if room in open_times:
                    open_time = open_times[room]
                    if open_time <= doc["bt"] <= close_time:
                        output["window_open"] = True
                        output["window_open_time"] = doc["bt"] - open_time

                outputs.append(output)

    return outputs


def gen_dataset_1(cleansed):
    temps = []
    hums = []

    for record in cleansed:
        if "temperature" in record:
            temps.append(record)
        if "humidity" in record:
            hums.append(record)

    with open("data/dataset_1/temperature.csv", "w+") as file:
        writer = csv.writer(file)
        writer.writerow([
            "time", "room", "temperature", "window_open", "window_open_time"
        ])
        for row in temps:
            writer.writerow([
                row["time"],
                row["room"],
                row["temperature"],
                row["window_open"],
                row["window_open_time"]
            ])

    with open("data/dataset_1/humidity.csv", "w+") as file:
        writer = csv.writer(file)
        writer.writerow([
            "time", "room", "humidity", "window_open", "window_open_time"
        ])
        for row in hums:
            writer.writerow([
                row["time"],
                row["room"],
                row["humidity"],
                row["window_open"],
                row["window_open_time"]
            ])


def gen_dataset_2(cleansed):
    temps = {room: [] for room in rooms}
    hums = {room: [] for room in rooms}

    for record in cleansed:
        if "temperature" in record:
            temps[record["room"]].append(record)
        if "humidity" in record:
            hums[record["room"]].append(record)

    for room in rooms:
        with open(f"data/dataset_2/{room}/temperature.csv", "w+") as file:
            writer = csv.writer(file)
            writer.writerow([
                "time", "temperature", "window_open", "window_open_time"
            ])
            for row in temps[room]:
                writer.writerow([
                    row["time"],
                    row["temperature"],
                    row["window_open"],
                    row["window_open_time"]
                ])

        with open(f"data/dataset_2/{room}/humidity.csv", "w+") as file:
            writer = csv.writer(file)
            writer.writerow([
                "time", "humidity", "window_open", "window_open_time"
            ])
            for row in hums[room]:
                writer.writerow([
                    row["time"],
                    row["humidity"],
                    row["window_open"],
                    row["window_open_time"]
                ])


def gen_datasets():
    cleansed = cleansed_data()
    gen_dataset_1(cleansed)
    gen_dataset_2(cleansed)


if __name__ == "__main__":
    sys.exit(gen_datasets())
