"""
Interact with gsheets for automation sake
"""

import sys
from configparser import ConfigParser
from typing import Dict

import gspread
import pandas as pd
from pandas.core.frame import DataFrame


def _get_config(config_file_path: str) -> Dict[str, str]:
    """
    gets the config file and loads the paths of relevant information
    """
    config = ConfigParser()
    config.read(config_file_path)
    return {
        "current_key": config["gsheets"]["current_key"],
        "old_key": config["gsheets"]["old_key"],
        "gisaid_wksht_num": int(config["gsheets"]["gisaid_wksht_num"]),
        "gsheet_key_path": config["gsheets"]["gsheet_key_path"],
    }


def gisaid_interactor(config_file_path: str, version: str = "current") -> pd.DataFrame:
    """
    Interact with a metadata file and get the appropriate results
    Split this out into separate file when we're done
    """
    config = _get_config(config_file_path)
    if version == "current":
        return _get_gsheet(
            config["current_key"], config["gisaid_wksht_num"], config["gsheet_key_path"]
        )
    elif version == "old":
        return _get_gsheet(
            config["old_key"], config["gisaid_wksht_num"], config["gsheet_key_path"]
        )
    #TODO: Fine tune this error
    else:
        raise ValueError

def zipcode_interactor(config_file_path: str) pd.DataFrame:
    """
    Gets all zipcode data for the samples and returns them
    """
    config = _get_config(config_file_path)
    current_zipcode_data = _get_gsheet(config["current_key"], config["zipcode_wksht_num"], config['gsheet_key_path'])[["SEARCH SampleID", "Zipcode"]]
    old_zipcode_data = _get_gsheet(config["old_key"], config["zipcode_wksht_num"], config['gsheet_key_path'])[["SEARCH SampleID", "Zipcode"]]

    return pd.concat([current_zipcode_data, old_zipcode_data])
    
def _get_gsheet(
    file_key: str, worksheet_num: int, service_account_json: str
) -> pd.DataFrame:
    """
    get from gsheetrm met
    """
    gc = gspread.service_account(filename=service_account_json)
    worksheet = gc.open_by_key(file_key).get_worksheet(worksheet_num)
    return pd.DataFrame(worksheet.get_all_records())


def _push_gsheet():
    """
    push data to gsheet
    """
    pass


if __name__ == "__main__":
    data = gisaid_interactor(sys.argv[1])
    data.to_csv(sys.argv[2], index=False)
