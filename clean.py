"""Generate cleansed datasets"""

import sys
import os
import csv
import json
from datetime import datetime, timedelta
from pymongo import MongoClient
import numpy as np

ROOMS = [
    "dining_room",
    "kitchen",
    "bathroom",
    "stairs",
    "bedroom",
    "hall",
    "living_room"
]

START = datetime(2018, 3, 21, 14)

OPEN_TIMES = {
    6: datetime(2018, 3, 21, 15, 15),
    4: datetime(2018, 3, 21, 15, 17),
    1: datetime(2018, 3, 21, 15, 41),
    2: datetime(2018, 3, 21, 16, 21)
}

CLOSE_TIME = datetime(2018, 3, 21, 16, 45)


def cleansed_data():
    """Connect to the database and cleanse and filter the data

    Returns:
        dict: the cleansed dataset

    """

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
                output["room"] = ROOMS[room]

                output["window_open"] = False
                output["window_open_time"] = 0

                if room in OPEN_TIMES:
                    open_time = OPEN_TIMES[room]
                    if open_time <= doc["bt"] < CLOSE_TIME:
                        output["window_open"] = True
                        output["window_open_time"] = doc["bt"] - open_time

                outputs.append(output)

    sorted_outputs = sorted(outputs, key=lambda rec: rec["time"])
    return sorted_outputs


def gen_dataset_1(cleansed):
    """Generate the first dataset, with CSVs for temperature and humidity
    for all rooms

    Args:
        cleansed (dict): The full cleansed dataset

    """

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
    """Generate the second dataset, with CSVs split up into rooms

    Args:
        cleansed (dict): the full cleansed dataset

    """

    temps = {room: [] for room in ROOMS}
    hums = {room: [] for room in ROOMS}

    for record in cleansed:
        if "temperature" in record:
            temps[record["room"]].append(record)
        if "humidity" in record:
            hums[record["room"]].append(record)

    for room in ROOMS:
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


def gen_dataset_3(cleansed):
    """Generate the third dataset, with CSVs for temperature and humidity
    grouped into thirty second bunches

    Args:
        cleansed (dict): the full cleansed dataset

    """

    start = datetime(2018, 3, 21, 14)
    end = datetime(2018, 3, 21, 18)
    delta = timedelta(seconds=30)

    rows = []

    time = start
    temp_group = {room: [] for room in ROOMS}
    hum_group = {room: [] for room in ROOMS}

    for rec in cleansed:
        room = rec["room"]

        while time < end and not (time <= rec["time"] < time + delta):
            for r in ROOMS:
                if temp_group[r] and hum_group[r]:
                    row = {}
                    row["time"] = time
                    row["room"] = r

                    row["window_open"] = False
                    row["window_open_time"] = 0

                    if ROOMS.index(r) in OPEN_TIMES:
                        open_time = OPEN_TIMES[ROOMS.index(r)]
                        if open_time <= time < CLOSE_TIME:
                            row["window_open"] = True
                            row["window_open_time"] = time - open_time

                    row["temperature"] = np.mean(temp_group[r])
                    row["humidity"] = np.mean(hum_group[r])
                    rows.append(row)

            time = time + delta
            temp_group = {room: [] for room in ROOMS}
            hum_group = {room: [] for room in ROOMS}

        if "temperature" in rec:
            temp_group[room].append(rec["temperature"])
        if "humidity" in rec:
            hum_group[room].append(rec["humidity"])

    with open("data/dataset_3/data.csv", "w+") as file:
        writer = csv.writer(file)
        writer.writerow([
            "time",
            "room",
            "temperature",
            "humidity",
            "window_open",
            "window_open_time"
        ])

        for row in rows:
            writer.writerow([
                row["time"],
                row["room"],
                row["temperature"],
                row["humidity"],
                row["window_open"],
                row["window_open_time"]
            ])


def gen_json(cleansed):
    """Generate the full cleansed dataset as JSON and save

    Args:
        cleansed (dict): the full cleansed dataset

    """

    def json_serial(obj):
        """ Converts date objects to a JSON acceptable format

        Args:
            obj (object): the incompatible object

        Returns:
            str: the object in a JSON-happy format

        """

        if isinstance(obj, datetime):
            return obj.isoformat()

        return str(obj)

    with open("data/all.json", "w+") as file:
        json.dump(cleansed, file, default=json_serial)


def gen_datasets():
    """Generate and save all of the cleansed datasets"""

    cleansed = cleansed_data()
    gen_dataset_1(cleansed)
    gen_dataset_2(cleansed)
    gen_dataset_3(cleansed)
    gen_json(cleansed)


if __name__ == "__main__":
    sys.exit(gen_datasets())
