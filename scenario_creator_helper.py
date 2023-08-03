"""
data.csv = Load flow from 2017-01-01
scenario.yml = created scenario
"""

import pandas as pd
import yaml


class ScenarioCreatorHelper:
    def create_scenario(self, config, input_path):
        df = pd.read_csv(input_path)
        df = df.drop(["Time"], axis=1)
        df = df.T
        yml_list = []

        df_backup = df
        for conf in config:
            df = df_backup.copy()
            for time_key in df.columns:
                time_from = f"{conf['day']}*24*60*60+{time_key}*900"
                time_to = f"{conf['day']}*24*60*60+{time_key}*900+899"
                df[time_key] = [f"{val}*{conf['factor']}" for val in df[time_key].values]

                yml_list.append([time_from, time_to, df[time_key].to_dict()])

        yaml.dump(yml_list, open("household_percentages/all_households_to_zero.yml", "w"))

helper = ScenarioCreatorHelper()
config = [
    {
        "day": 0,
        "factor": 0.0
    },
]
helper.create_scenario(config, "loads_household.csv")
