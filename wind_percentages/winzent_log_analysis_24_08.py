import os
import sys
import csv
from os.path import exists
import ast

"""
Script to analyze the log file of winzent experiments 
which prints out and/or writes information about the runtime, negotiation quality and the amount of messages
in a .csv-file.
The string readouts are set for the log file version that is implemented in the 
"PGASC-Winzent-Changes" (commit: 7a76cd2a, 18.08.2022) branch in the mango-library repository.

Usage:
python winzent_log_analysis.py <<log file path>> <<Boolean to write results into .csv-files>>

If none of the parameters are specified, the script will analyze all .log-files in the current 
working directory and write them into a .csv-file.
"""


def calc_runtime(file_name):
    """
    Returns a dict that contains the average runtime over all steps taken as well as
    the max. and the min. runtime.
    """
    runtime = {
        "min": 0.0,
        "max": 0.0,
        "avg": 0.0
    }
    step_counter = 0
    with open(file_name, encoding="utf8") as temp_f:
        datafile = temp_f.readlines()
    for line in datafile:
        if 'Runtime: ' in line:
            curr_runtime = float(line.split(' ')[1])
            if runtime["min"] > curr_runtime or runtime["min"] == 0.0:
                runtime["min"] = curr_runtime
            if runtime["max"] < curr_runtime or runtime["min"] == 0.0:
                runtime["max"] = curr_runtime
            step_counter += 1
            runtime["avg"] += curr_runtime
    if step_counter > 0:
        runtime["avg"] = runtime["avg"] / step_counter
    else:
        runtime["avg"] = 0
    return runtime


def calc_messages(file_name):
    """
    Returns a dict that contains the average amount of messages over all steps taken as well as
    the max. and the min. amount of messages.
    """
    messages = {
        "min": 0.0,
        "max": 0.0,
        "avg": 0.0
    }
    step_counter = 0
    with open(file_name, encoding="utf8") as temp_f:
        datafile = temp_f.readlines()
    for line in datafile:
        if 'Messages sent: ' in line:
            curr_messages = float(line.split(' ')[2])
            if messages["min"] > curr_messages or messages["min"] == 0.0:
                messages["min"] = curr_messages
            if messages["max"] < curr_messages or messages["min"] == 0.0:
                messages["max"] = curr_messages
            step_counter += 1
            messages["avg"] += curr_messages
    if step_counter > 0:
        messages["avg"] = messages["avg"] / step_counter
    else:
        messages["avg"] = 0
    return messages


def calc_negotiation_percent(file_name):
    """
    Returns a dict that contains the average negotiation result
    ((amount of negotiated power / power needed by loads)) over all steps taken as well as
    the max. and the min. negotiation result.
    """
    neg_pct = {
        'min': 0.0,
        'max': 0.0,
        'avg': 0.0
    }
    step_counter = 0
    needed_loads = -1
    with open(file_name, encoding="utf8") as temp_f:
        datafile = temp_f.readlines()
    for line in datafile:
        if 'Needed Loads: ' in line:
            step_counter += 1
            needed_loads = float(line.split(' ')[2])
            continue
        if needed_loads > -1:
            neg_value = float(line.split(' ')[4])
            curr_neg_pct = neg_value / needed_loads
            neg_pct['avg'] += curr_neg_pct
            if neg_pct["min"] > curr_neg_pct or neg_pct["min"] == 0.0:
                neg_pct["min"] = curr_neg_pct
            if neg_pct["max"] < curr_neg_pct or neg_pct["min"] == 0.0:
                neg_pct["max"] = curr_neg_pct
            needed_loads = -1
    if step_counter > 0:
        neg_pct['avg'] = neg_pct['avg'] / step_counter
    else:
        neg_pct['avg'] = 0
    return neg_pct


def calc_ethics_score(file_name):
    """
    Returns a dict that contains the average negotiation result
    ((amount of negotiated power / power needed by loads)) over all steps taken as well as
    the max. and the min. negotiation result.
    """
    full_ethics_scores = {}
    step_counter = 0
    with open(file_name, encoding="utf8") as temp_f:
        datafile = temp_f.readlines()
    for line in datafile:
        if 'ethics_scores' in line:
            step_counter += 1
            ethics_scores = ast.literal_eval(line.split('-->')[1])
            if not full_ethics_scores:
                full_ethics_scores = ethics_scores
            else:
                for key in full_ethics_scores:
                    full_ethics_scores[key] = [a + b for a, b in zip(full_ethics_scores[key], ethics_scores[key])]
            continue
    final_ethics_scores = {}
    for key in full_ethics_scores:
        final_ethics_scores[key] = [(full_ethics_scores[key][0] / float(full_ethics_scores[key][2])), full_ethics_scores[key][1]]
    return final_ethics_scores


def check_for_warnings(file_name):
    warning_counter = 0
    with open(file_name, encoding="utf8") as temp_f:
        datafile = temp_f.readlines()
    for line in datafile:
        if 'Invalid' in line:
            warning_counter += 1
    return warning_counter


def check_energy(file_name):
    step_counter = 0
    produced_counter = {}
    energy_absolute = {}
    energy_scaling = {}
    energy_percent = {}
    energy_scaling_percent = {}
    with open(file_name, encoding="utf8") as temp_f:
        datafile = temp_f.readlines()
    total_power_produced_this_step = 0
    for line in datafile:
        if 'PRODUCED' in line:
            if line.split(' ')[2] in energy_absolute:
                total_power_produced_this_step += int(line.split(' ')[1])
                energy_absolute[line.split(' ')[2]] += int(line.split(' ')[1])
                energy_scaling[line.split(' ')[2]] += float(line.split(' ')[3])
                produced_counter[line.split(' ')[2]] += 1
            else:
                total_power_produced_this_step += int(line.split(' ')[1])
                energy_absolute[line.split(' ')[2]] = int(line.split(' ')[1])
                energy_scaling[line.split(' ')[2]] = float(line.split(' ')[3])
                produced_counter[line.split(' ')[2]] = 1
        if 'Needed Loads:' in line:
            total_value = float(line.split(' ')[2])
            energy_absolute['ext_grid'] = total_value - total_power_produced_this_step
            energy_scaling['ext_grid'] = 1
            produced_counter['ext_grid'] = 1
            total_power_produced_this_step = 0
            if total_value > 0:
                for energy_type in energy_absolute:
                    if energy_type in energy_percent:
                        energy_percent[energy_type] += energy_absolute[energy_type] / total_value
                        if produced_counter[energy_type] > 0:
                            energy_scaling_percent[energy_type] += energy_scaling[energy_type] / produced_counter[energy_type]
                    else:
                        energy_percent[energy_type] = energy_absolute[energy_type] / total_value
                        energy_scaling_percent[energy_type] = energy_scaling[energy_type] / produced_counter[energy_type]
                    produced_counter[energy_type] = 0
                    energy_absolute[energy_type] = 0
                    energy_scaling[energy_type] = 0
            step_counter += 1
    for key in energy_percent:
        energy_percent[key] = energy_percent[key] / step_counter
        energy_scaling_percent[key] = energy_scaling_percent[key] / step_counter
    return energy_percent, energy_scaling_percent


def put_results_into_csv(messages, runtime, negotiation_results, ethics_scores, warnings,
                         energy_percent,
                         energy_scaling_percent,
                         filename,
                         log_name):
    if 'Wind' not in energy_percent:
        energy_percent["Wind"] = 0
        energy_scaling_percent["Wind"] = 0
    if 'Abfall' not in energy_percent:
        energy_percent['Abfall'] = 0
        energy_scaling_percent['Abfall'] = 0
    if 'gas' not in energy_percent:
        energy_percent['gas'] = 0
        energy_scaling_percent['gas'] = 0
    if 'PV' not in energy_percent:
        energy_percent['PV'] = 0
        energy_scaling_percent['PV'] = 0
    if 'ext_grid' not in energy_percent:
        energy_percent['ext_grid'] = 0
        energy_scaling_percent['ext_grid'] = 0
    data_list = {"log_name": log_name,
                 "max. runtime": runtime['max'],
                 "min_runtime": runtime['min'],
                 "avg_runtime": runtime['avg'],
                 "max_messages": messages['max'],
                 "min_messages": messages['min'],
                 "avg_messages": messages['avg'],
                 "max. neg": negotiation_results['max'],
                 "min. neg": negotiation_results['min'],
                 "avg. neg": negotiation_results['avg'],
                 "warnings": warnings,
                 "Wind": energy_percent["Wind"],
                 "Abfall": energy_percent["Abfall"],
                 "gas": energy_percent["gas"],
                 "PV": energy_percent["PV"],
                 "ext_grid": energy_percent["ext_grid"],
                 "used_Wind_potential": energy_scaling_percent["Wind"],
                 "used_Abfall_potential": energy_scaling_percent["Abfall"],
                 "used_gas_potential": energy_scaling_percent["gas"],
                 "used_PV_potential": energy_scaling_percent["PV"],
                 }
    for key in ethics_scores:
        data_list[str(key)] = ethics_scores[key][0]
        data_list[str(key)+"_outages"] = ethics_scores[key][1]
    fieldnames = data_list.keys()
    file_exists = os.path.isfile(filename + ".csv")
    with open(filename + ".csv", 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_list)


def main():
    try:
        log_name = str(sys.argv[1])
    except:
        log_name = 'all'
        print("All .log-files in this folder will be analyzed.")
    try:
        write_to_csv = sys.argv[2]
    except:
        write_to_csv = True
        print("Results will be written to .csv.")
    curr_dir = str(os.getcwd())
    for file in os.listdir(curr_dir):
        filename = os.fsdecode(file)
        if filename.endswith(".log"):
            if log_name != 'all':
                filename = log_name
            messages = calc_messages(filename)
            runtime = calc_runtime(filename)
            negotiation_results = calc_negotiation_percent(filename)
            ethics_scores = calc_ethics_score(filename)
            warnings = check_for_warnings(filename)
            energy_percent, energy_scaling_percent = check_energy(filename)
            if write_to_csv == True:
                put_results_into_csv(messages, runtime, negotiation_results, ethics_scores,
                                     warnings, energy_percent,
                                     energy_scaling_percent,
                                     "winzent_log_results", filename)
            else:
                print(f"Results for {str(filename)}:")
                print(f"max. runtime: {runtime['max']}\n"
                      f"min. runtime: {runtime['min']}\n"
                      f"avg. runtime {runtime['avg']}")
                print(f"max. messages: {messages['max']}\n"
                      f"min. messages: {messages['min']}\n"
                      f"avg. messages: {messages['avg']}")
                print(f"max. neg: {negotiation_results['max']}\n"
                      f"min. neg: {negotiation_results['min']}\n"
                      f"avg. neg: {negotiation_results['avg']}")
                for score in ethics_scores.keys():
                    print(f"ethics score for {score}: {ethics_scores[score]}\n")
                print(f"amount of warnings: {warnings}")
                for key in energy_percent:
                    print(f"Energy mix had {energy_percent[key] * 100} % of "
                          f"{key} energy in it. This was {energy_scaling_percent[key] * 100} % of the "
                          f"possible max.")
            if log_name != 'all':
                break
            else:
                continue
        else:
            continue


if __name__ == "__main__":
    main()
    print("Desired .log-files have been successfully analyzed.")
