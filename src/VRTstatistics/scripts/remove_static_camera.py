import math
import json
import sys

from collections import defaultdict
from functools import reduce
from operator import itemgetter
from typing import Optional


def get_cameras(data):
    def reduce_cameras(acc, record):
        if record["component"].startswith("PositionTracker#Camera"):
            acc[record["component"]].append(record)

        return acc

    return reduce(reduce_cameras, data, defaultdict(list))


def get_camera_movement(camera_data) -> float:
    total_dist = 0.0

    for i, record in enumerate(camera_data[:-1]):
        next_record = camera_data[i+1]
        total_dist += math.sqrt(
            math.pow(next_record["px"] - record["px"], 2) +
            math.pow(next_record["py"] - record["py"], 2) +
            math.pow(next_record["pz"] - record["pz"], 2)
        )

    return total_dist


def get_observer_camera(camera_data) -> str:
    distances = [(k, get_camera_movement(v)) for k, v in camera_data.items()]
    return sorted(distances, key=itemgetter(1))[0][0]


def main(infile: str, outfile: Optional[str] = None) -> None:
    with open(infile, "r") as f:
        data = json.load(f)
        camera_data = get_cameras(data)

        observer_key = get_observer_camera(camera_data)
        filtered_data = [
            record for record in data
            if record["component"] != observer_key
        ]

        if outfile is None:
            print(json.dumps(filtered_data))
        else:
            with open(outfile, "w") as f:
                json.dump(filtered_data, f)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("USAGE:", sys.argv[0], "input_json [output_json]")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = None

    if len(sys.argv) == 3:
        outfile = sys.argv[2]

    main(infile, outfile)
