"""
S3CAR Global configuration class.
"""
__authors__ = "Valentin Louf"
__contact__ = "valentin.louf@bom.gov.au"
__version__ = "0.5.0"
__date__ = "2021/06"

import os
import time

import pandas as pd


class S3car():
    def __init__(self, root_dir="/srv/data/s3car-server", etc_dir="/etc/opt/s3car-server/", html_dir="/srv/web/s3car-server/www") -> None:
        self.root_path = root_dir
        self.cluttercal_path = os.path.join(root_dir, "cluttercal")
        self.config_path = os.path.join(root_dir, "config")
        self.clean_ts_path = os.path.join(root_dir, "s3car_diagnostics", "clean")
        self.diagnostics_path = os.path.join(root_dir, "s3car_diagnostics", "diagnostics")
        self.raw_ts_path = os.path.join(root_dir, "s3car_diagnostics", "raw")
        self.dualpolqc_path = os.path.join(root_dir, "dualpol_qc")
        self.gpmmatch_path = os.path.join(root_dir, "gpmmatch")
        self.html_path = html_dir
        self.log_path = os.path.join(root_dir, "log")
        self.solar_path = os.path.join(root_dir, "solar", "data")
        self.vols_path = os.path.join(root_dir, "vols")
        self.zdr_path = os.path.join(root_dir, "zdr_monitoring")

        self.tier1_radars = [2, 3, 4, 8, 19, 22, 23, 24, 28, 40, 52, 63, 64, 66, 68, 70, 71, 73, 76]

        self.zdr_range = (-2, 2)  # ZDR min/max for histogram.
        self.zdr_step = abs(0.08)  # ZDR resolution in dB
        self.zdr_bins = int(round((self.zdr_range[1] - self.zdr_range[0]) / self.zdr_step))

        self.check_paths_exist()
        self.set_radar_site_info()

    def check_paths_exist(self):
        for k, v in self.__dict__.items():
            if "path" in k:
                if not os.path.exists(v):
                    raise FileNotFoundError(f"Directory {v} not found.")

    def get_lat(self, rid: int) -> float:
        """
        Get latitude for given radar ID.
        Parameter:
        ==========
        rid: int
            Radar Rapic ID
        Returns:
        ========
        latitude: float
            Radar site latitude
        """
        return self.radar_site_info.loc[self.radar_site_info.id == rid].site_lat.values[0]

    def get_lon(self, rid: int) -> float:
        """
        Get longitude for given radar ID.
        Parameter:
        ==========
        rid: int
            Radar Rapic ID
        Returns:
        ========
        longitude: float
            Radar site longitude
        """
        return self.radar_site_info.loc[self.radar_site_info.id == rid].site_lon.values[0]

    def set_radar_site_info(self):
        radar_fname = os.path.join(self.config_path, "radar_site_list.csv")
        self.radar_site_info = pd.read_csv(radar_fname)
        if len(self.radar_site_info) == 0:
            raise ValueError(f"Invalid radar configuration file: {radar_fname}. Exiting code.")


class Chronos:
    """
    https://www.youtube.com/watch?v=QcHvzNBtlOw
    """

    def __init__(self, messg=None):
        self.messg = messg

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, ntype, value, traceback):
        self.time = time.time() - self.start
        if self.messg is not None:
            print(f"{self.messg} took {self.time:.2f}s.")
        else:
            print(f"Processed in {self.time:.2f}s.")