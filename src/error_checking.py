import pandas as pd
from alab_release import process_id

def date_range_check(data: pd.DataFrame):
    # confirm that all dates are between 1/1/2020 and today
    date_range = pd.Series(pd.date_range('2020-1-1', pd.to_datetime("today")))
    data["Collection date"] = pd.to_datetime(data["Collection date"])
    test_frame = data[~data["Collection date"].isin(date_range)]
    if len(test_frame) > 0:
        print(test_frame)
        raise Exception("Error: metadata date range out of assigned limits - check metadata")
    else:
        return

def date_agreement_check(data: pd.DataFrame):
    # confirm that the years in the virus name match the year in the collection date
    data["virus_year"] = [item.split("/")[-1] for item in data["Virus name"]]
    data["Collection date"] = pd.to_datetime(data["Collection date"])
    data["collection_year"] = [str(item.year) for item in data["Collection date"]]]]
    test_frame = data[~(data["virus_year"] == data["collection_year"])]
    if len(test_frame) > 0:
        print(test_frame)
        raise Exception("Error: collection year does not match year assigned to samples - check metadata")
    else:
        return

def sample_id_check(data: pd.DataFrame):
    data["virus_name_id"] = [process_id(item.split("/")[-2]) for item in data["Virus name"]]
    data["sample_id"] = [process_id(item) for item in data["SEARCH SampleID"]]
    test_frame = data[~(data["virus_name_id"] == data["sample_id"])]
    if len(test_frame) > 0:
        print(test_frame)
        raise Exception("Error: virus name does not match sample id name - check metadata")
    else:
        return