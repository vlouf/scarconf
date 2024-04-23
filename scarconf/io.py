import os
import re
import itertools
from datetime import datetime

import h5py
from typing import AnyStr


class ODIMFileInfo:
    """
    Extracts and provides information about a radar data file.

    Attributes:
        - filename (str): The path to the radar data file.
        - rid (int): Radar ID extracted from the filename.
        - lat (float): Latitude information from the radar data file.
        - lon (float): Longitude information from the radar data file.
        - datetime (datetime): Date and time information from the radar data file.
        - moments (list): List of radar moments extracted from the dataset.

    Methods:
        - __init__(self, input_file: AnyStr) -> None:
            Initializes the FileInformation object by checking the input file, extracting radar ID,
            and setting additional information.

        - check_input_file(self, incoming_data: AnyStr) -> str:
            Checks the input file, decodes if necessary, and validates its existence and size.

        - set_infos(self) -> None:
            Extracts latitude, longitude, date, time, and radar moments from the radar data file.

        - get_rid(self) -> int:
            Extracts and validates the radar ID from the filename.

    Note: The class provides information about a radar data file and its attributes and methods.
    """

    def __init__(self, input_file) -> None:
        self.filename = self.check_input_file(input_file)
        self.rid = self.get_rid()
        self.set_infos()

    def check_input_file(self, incoming_data: AnyStr) -> str:
        if type(incoming_data) is str:
            filename = incoming_data
        else:
            filename = incoming_data.decode("utf-8")

        if not os.path.isfile(filename):
            raise FileNotFoundError(f"File: {filename} does not exist.")
        elif os.stat(filename).st_size == 0:
            raise FileExistsError(f"File: {filename} is 0 byte in size.")
        else:
            return filename

    def set_infos(self) -> None:
        var = []
        with h5py.File(self.filename) as odim:
            self.lat = odim["where"].attrs["lat"]
            self.lon = odim["where"].attrs["lon"]
            date = odim["what"].attrs["date"].decode()
            time = odim["what"].attrs["time"].decode()
            ds1 = odim["dataset1"]
            for dt_idx in itertools.count(1):
                if not f"data{dt_idx}" in ds1:
                    break  # all moments done
                name = ds1[f"data{dt_idx}/what"].attrs["quantity"].decode()
                var.append(name)

        self.datetime = datetime.strptime(f"{date}{time}", "%Y%m%d%H%M%S")
        self.moments = var

    def get_rid(self) -> int:
        try:
            rid = int(re.match(r"\d+", os.path.basename(self.filename)).group(0))
        except:
            raise ValueError(f"Bad filename (no radar ID found) for path {self.filename}")
        if rid <= 0 or rid > 1000:
            raise ValueError(f"Bad radar ID {rid} for path {self.filename}")
        return rid
