import pandas as pd

def date_range_check(data: pd.DataFrame):
    # confirm that all dates are between 1/1/2020 and today
    date_range = pd.Series(pd.date_range('2020-1-1', pd.to_datetime("today")))
    data["covv_collection_date"] = pd.to_datetime(data["covv_collection_date"])
    test_frame = data[~data["covv_collection_date"].isin(date_range)]
    if len(test_frame) > 0:
        print(test_frame)
        raise Exception("Error: metadata date range out of assigned limits - check metadata")
    else:
        return

def date_agreement_check(data: pd.DataFrame):
    # confirm that the years in the virus name match the year in the collection date
    data["virus_year"] = [item.split("/")[-1] for item in data["covv_virus_name"]]
    data["covv_collection_date"] = pd.to_datetime(data["covv_collection_date"])
    data["collection_year"] = [str(item.year) for item in data["covv_collection_date"]]
    test_frame = data[~(data["virus_year"] == data["collection_year"])]
    if len(test_frame) > 0:
        print(test_frame)
        raise Exception("Error: collection year does not match year assigned to samples - check metadata")
    else:
        return

def sample_id_check():
    #TODO: Add checking to make sure virus number and sample number match up, and that sample ids are unique
    pass