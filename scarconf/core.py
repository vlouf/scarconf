"""
S3CAR Global configuration class.
"""
__authors__ = "Valentin Louf"
__contact__ = "valentin.louf@bom.gov.au"
__version__ = "0.5.0"
__date__ = "2021/06"

import configparser
import logging
import math
import os
import time

import pandas as pd


class S3car():
    def __init__(self,
                 root_dir="/srv/data/s3car-server",
                 etc_dir="/etc/opt/s3car-server/",
                 html_dir="/srv/web/s3car-server/www",
                 read_radars=True,
                 ) -> None:

        try:
            # env override of root directory
            s3car_root = os.environ["S3CAR_ROOT_DIR"]
            # prefix all directories
            root_dir = s3car_root + root_dir
            etc_dir = s3car_root + etc_dir
            html_dir = s3car_root + html_dir
        except KeyError:
            pass

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
        self.sst_path = os.path.join(root_dir, "sensitivity")
        self.vols_path = os.path.join(root_dir, "vols")
        self.zdr_path = os.path.join(root_dir, "zdr_monitoring")
        self.zdr_range = (-2, 2)  # ZDR min/max for histogram.
        self.zdr_step = abs(0.08)  # ZDR resolution in dB
        self.zdr_bins = int(round((self.zdr_range[1] - self.zdr_range[0]) / self.zdr_step))

        # defaults #
        self._init_longname_default()
        self.country_code = "AU"
        self.gpm_userid = ""
        self.gpm_requestid = "001"
        self.rainptl_enabled = True
        self.region = {
            'lat': (-46.0, -7.5),
            'lon': (112.0, 155.0),
        }
        # TODO: consider having per-radar.tier instead of exhaustive list here
        self.tier1_radars = [2, 3, 4, 8, 19, 22, 23, 24, 28, 40, 52, 63, 64, 66, 68, 70, 71, 73, 76]
        self.tier2_radars = [1, 5, 6, 7, 14, 15, 16, 17, 29, 31, 32, 38, 42, 46, 49, 50, 55, 58, 67,
                             69, 72, 74, 75, 77, 78, 79, 93, 94, 95, 96, 98, 107, 108, 109, 110]
        self.tier3_radars = [9, 10, 25, 26, 27, 30, 33, 36, 37, 39, 41, 44, 48, 53, 54, 56, 62, 97]
        self.censor_radars = [30, 100, 101, 102, 103, 104]
        self.nosun_radars = [6, 31, 32, 48, 95]

        self.read_local_config(etc_dir)
        self.calc_region()

        self.check_paths_exist()
        if read_radars:
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

    def get_radar_tier(self, rid: int) -> int:
        """
        Get radar tier

        Parameter:
        ==========
        rid: int
            Radar rapic ID

        Returns
        =======
        tier: int
            Tier 1, 2, 3 or 0 for unknown.
        """
        if rid in self.tier1_radars:
            return 1
        if rid in self.tier2_radars:
            return 2
        if rid in self.tier3_radars:
            return 3
        return 0

    def set_radar_site_info(self):
        radar_fname = os.path.join(self.config_path, "radar_site_list.csv")
        self.radar_site_info = pd.read_csv(radar_fname)
        if len(self.radar_site_info) == 0:
            raise ValueError(f"Invalid radar configuration file: {radar_fname}. Exiting code.")

    def calc_region(self):
        # for converting lat,lon pairs use pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857")
        eq_radius = 6378137
        def delta(t): return t[1] - t[0]
        def lon2mx(lon): return eq_radius * math.radians(lon)
        def lat2my(lat): return eq_radius * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

        # derived region vals used in dashboard / make_bokeh_map()
        self.region['mercator_x'] = tuple(lon2mx(lon) for lon in self.region['lon'])
        self.region['mercator_y'] = tuple(lat2my(lat) for lat in self.region['lat'])
        aspect_xy = delta(self.region['mercator_x']) / delta(self.region['mercator_y'])
        self.region['aspect_ratio'] = aspect_xy

    def read_local_config(self, etc_dir):
        """Read local configuration settings (if any)."""

        # load local.conf #

        cfg_path = os.path.join(etc_dir, "local.conf")
        cfg = configparser.ConfigParser()
        try:
            cfg.read(cfg_path)
        except:
            return

        # use local config #

        # [country]
        if have_config(cfg, 'country', 'code'):
            self.country_code = cfg['country']['code']
        # [gpm]
        if have_config(cfg, 'gpm', 'userid'):
            self.gpm_userid = cfg['gpm']['userid']
        if have_config(cfg, 'gpm', 'requestid'):
            self.gpm_requestid = cfg['gpm']['requestid']
        # [rainptl]
        if have_config(cfg, 'rainptl', 'enable'):
            self.rainptl_enabled = cfg['rainptl'].getboolean('enable')
        # [radar]
        if have_config(cfg, 'radar', 'tier1'):
            self.tier1_radars = config_list(cfg, int, 'radar', 'tier1')
        if have_config(cfg, 'radar', 'tier2'):
            self.tier2_radars = config_list(cfg, int, 'radar', 'tier2')
        if have_config(cfg, 'radar', 'tier3'):
            self.tier3_radars = config_list(cfg, int, 'radar', 'tier3')
        if have_config(cfg, 'radar', 'censor'):
            self.censor_radars = config_list(cfg, int, 'radar', 'censor')
        if have_config(cfg, 'radar', 'nosun'):
            self.nosun_radars = config_list(cfg, int, 'radar', 'nosun')
        # [region]
        if have_config(cfg, 'region', 'lat'):
            self.region['lat'] = tuple(config_list(cfg, float, 'region', 'lat'))
        if have_config(cfg, 'region', 'lon'):
            self.region['lon'] = tuple(config_list(cfg, float, 'region', 'lon'))

        # individual radar info [radar.ID]
        if have_config(cfg, 'radar', 'ids'):
            radar_ids = config_list(cfg, int, 'radar', 'ids')
            for rid in radar_ids:
                if not self.get_radar_tier(rid):
                    print(f"No tier for radar {rid} configured")
                stanza = f"radar.{rid}"
                if not stanza in cfg:
                    print(f"No configuration {stanza} entry found")
                    continue
                if have_config(cfg, stanza, 'longname'):
                    self.radar_longname[rid] = cfg[stanza]['longname']

    def get_radar_longname(self, rid: int) -> str:
        """
        If existing, returns the longname for the radar location.

        Parameters:
        ===========
        rid: int
            Radar ID.

        Returns:
        ========
        longname: str
            Radar location name.
        """
        try:
            return self.radar_longname[rid]
        except KeyError:
            return None

    def _init_longname_default(self):
        """Initialise longname map."""
        self.radar_longname = {
        1: "Melbourne (Broadmeadows)",
        2: "Melbourne",
        3: "Wollongong (Appin)",
        4: "Newcastle",
        5: "Carnarvon",
        6: "Geraldton",
        7: "Wyndham",
        8: "Gympie (Mt Kanigan)",
        9: "Gove",
        10: "Darwin Airport",
        14: "Mt Gambier",
        15: "Dampier",
        16: "Pt Hedland",
        17: "Broome",
        19: "Cairns",
        22: "Mackay",
        23: "Gladstone",
        24: "Bowen",
        25: "Alice Springs",
        26: "Perth Airport",
        27: "Woomera",
        28: "Grafton",
        29: "Learmonth",
        30: "Mildura",
        31: "Albany",
        32: "Esperance",
        33: "Ceduna",
        36: "Gulf of Carpentaria (Mornington Is)",
        37: "Hobart Airport",
        38: "Newdegate",
        39: "Halls Creek",
        40: "Canberra (Captains Flat)",
        41: "Willis Island",
        42: "Katherine (Tindal)",
        44: "Giles",
        46: "Adelaide (Sellicks Hill)",
        48: "Kalgoorlie",
        49: "Yarrawonga",
        50: "Brisbane (Marburg)",
        52: "N.W. Tasmania (West Takone)",
        53: "Moree",
        54: "Sydney (Kurnell)",
        55: "Wagga Wagga",
        56: "Longreach",
        58: "South Doodlakine",
        62: "Norfolk Island",
        63: "Darwin (Berrimah)",
        64: "Adelaide (Buckland Park)",
        66: "Brisbane (Mt Stapylton)",
        67: "Warrego",
        68: "Bairnsdale",
        69: "Namoi (Blackjack Mountain)",
        70: "Perth (Serpentine)",
        71: "Sydney (Terrey Hills)",
        72: "Emerald",
        73: "Townsville (Hervey Range)",
        74: "Greenvale",
        75: "Mount Isa",
        76: "Hobart (Mt Koonya)",
        77: "Warruwi",
        78: "Weipa",
        79: "Watheroo",
        93: "Brewarrina",
        94: "Hillston",
        95: "Rainbow (Wimmera)",
        96: "Yeoval",
        97: "Mildura",
        98: "Taroom",
        105: "Brisbane Airport",
        107: "Richmond",
        108: "Darling Downs",
        109: "Goondiwindi",
        110: "Tennant Creek",
    }

    def configure_logging(self, level=logging.INFO):
        """Configure logging setup."""
        # TODO: vary according to config

        # add time to log_fmt if running in apptainer/singularity
        log_fmt="%(levelname)s %(message)s"
        if os.environ.keys() & {'APPTAINER_CONTAINER', 'SINGULARITY_CONTAINER'}:
            log_fmt="%(asctime)s " + log_fmt
        logging.basicConfig(
            level=level,
            format=log_fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

def have_config(cfg, group, item):
    """Return True if cfg[group][item] exists."""
    return cfg and group in cfg and item in cfg[group]

def config_list(cfg, ty, group, item):
    """Return cfg[group][item] as list of type `ty`."""
    if not cfg[group][item]:
        return []
    return [ty(r) for r in cfg[group][item].split(' ')]

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
