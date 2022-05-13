"""
This file takes an updated metadata.csv file, generates a new location summary,
and accordingly updates the repo readme
"""

import pandas as pd
import os
import sys


def generate_location_summary_table(
    metadata: str, out_file: str, location_combination_config: str
):
    """
    Takes the current metadata file path, a destination file path, and a file
    which specifies how to combine locations to generate a new markdown table
    summarizing the number of sequences from given locations
    """
    # read file
    df = pd.read_csv(metadata)
    # generate locations df
    locations = pd.DataFrame(df.location.value_counts()).dropna()
    locations.index.rename("Location", inplace=True)
    locations.rename(columns={"location": "Number of Sequences"}, inplace=True)
    location_dict = locations.to_dict(orient='index')
    for key in location_dict: 
        location_dict[key]["corrected_location"] = "/".join(key.split("/")[1:])
    cleaned_locations = pd.Dataframe.from_dict(location_dict, orient='index').reset_index(drop=True)
    consolidated_location_data = (
        cleaned_locations.groupby(["corrected_location"], as_index=False)
        .agg({"Number of Sequences": "sum"})
        .rename(columns={"corrected_location": "Location"})
        .set_index("Location")
        .sort_index(kind="stable")
    )
    # write dataframe to a a markdown table
    with open(out_file, "w") as out:
        out.write(consolidated_location_data.to_markdown())
    return


def update_and_combine_readme(
    metadata_md: str, readme_md: str, new_readme_path: str, initial_buffer: int, ending_buffer: int
) -> None:
    """
    Takes the current readme, updates it with new table info
    """
    with open(new_readme_path, "w") as new_readme:
        # get the current readme header
        with open(readme_md, "r") as current_readme:
            head = current_readme.readlines()[:initial_buffer]
        new_readme.writelines(head)
        # get the new metadata table
        with open(metadata_md, "r") as location_table:
            for line in location_table:
                new_readme.write(line)
        # write an extra new line to separate table from tail
        new_readme.write("\n")
        # get the current readme tail
        with open(readme_md, "r") as current_readme:
            tail = current_readme.readlines()[ending_buffer:]
        new_readme.writelines(tail)
    return

def main(folder_path: str) -> None:
    # generate new files and updated readme
    generate_location_summary_table(
        os.path.join(folder_path, "metadata.csv"),
        os.path.join(folder_path, "metadata_location_summaries.md"),
        os.path.join(folder_path, "location_consolidation_mapping.csv"),
    )
    update_and_combine_readme(
        os.path.join(folder_path, "metadata_location_summaries.md"),
        os.path.join(folder_path, "README.md"),
        os.path.join(folder_path, "new_readme.md"),
        initial_buffer=5,
        ending_buffer=-20,
    )
    # rename current readme to OLD_readme,new readme to README.md
    os.rename(os.path.join(folder_path, "README.md"), os.path.join(folder_path, "OLD_README.md"))
    os.rename(os.path.join(folder_path, "new_readme.md"), os.path.join(folder_path, "README.md"))
    os.remove(os.path.join(folder_path, "metadata_location_summaries.md"))
    return


if __name__ == "__main__":
    main(sys.argv[1])
