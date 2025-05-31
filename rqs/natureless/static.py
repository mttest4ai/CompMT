import pandas as pd
import os
import json
from sklearn.metrics import cohen_kappa_score
import numpy as np
import time

def write_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=3)

def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# read xlsx file
def read_xlsx(file_path):
    data = pd.read_excel(file_path, header=None)
    return data

def compute_kappa_score(error1, error2):
    error1 = np.array(error1)
    error2 = np.array(error2)
    return cohen_kappa_score(error1, error2)

if __name__ == "__main__":
    folder_path = "./results"
    team_folders = ["member1", "member2"]
    
    mutants = ["mutant_1", "mutant_2", "mutant_3"]
    label_dict = dict()
    for i in range(len(mutants)):
        label_dict[mutants[i]] = dict()
        label_dict[mutants[i]]["member1"] = []
        label_dict[mutants[i]]["member2"] = []

    datasets = ["manual_humaneval", "manual_mbpp"]
    output_folder = f"{folder_path}/manual_result"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    
    for dataset in datasets:
        if not os.path.exists(f"{output_folder}/{dataset}"):
            os.makedirs(f"{output_folder}/{dataset}")
        for mutant in mutants:
            data1 = read_xlsx(f"{folder_path}/{team_folders[0]}/{dataset}/combine_nature_{mutant}_item.xlsx")
            data2 = read_xlsx(f"{folder_path}/{team_folders[1]}/{dataset}/combine_nature_{mutant}_item.xlsx")
            assert len(data1) == len(data2)
            data1_labels = []
            data2_labels = []
            result = dict()
            for k, row in data1.iterrows():
                if k == 0:
                    continue
                task_id = row.values[0]
                prompt = row.values[1]
                comb_test = row.values[2]
                label = row.values[3]
                data1_labels.append(label)
                if not task_id in result:
                    result[task_id] = dict()
                    result[task_id]["prompt"] = prompt
                    result[task_id]["comb_test"] = comb_test
                    result[task_id]["label1"] = label
            for k, row in data2.iterrows():
                if k == 0:
                    continue
                task_id = row.values[0]
                prompt = row.values[1]
                comb_test = row.values[2]
                label = row.values[3]
                data2_labels.append(label)
                result[task_id]["label2"] = label
                if result[task_id]["label1"] == result[task_id]["label2"]:
                    result[task_id]["final_result"] = result[task_id]["label1"]
                else:
                    result[task_id]["final_result"] = "futher check needed"
            # if result json file not exist, create it, else, give up
            if not os.path.exists(f"{output_folder}/{dataset}/{mutant}_conflict_solved.json"):
                write_json(result, f"{output_folder}/{dataset}/{mutant}_conflict_solved.json")
            label_dict[mutant]["member1"].extend(data1_labels)
            label_dict[mutant]["member2"].extend(data2_labels)
    # compute kappa score
    kappa_result = dict()
    for mutant in mutants:
        error1 = label_dict[mutant]["member1"]
        error2 = label_dict[mutant]["member2"]
        # float is not supported in cohen_kappa_score, convert to int, error list contains 1, 0, 0.5
        mapping = {0: 0, 0.5: 1, 1: 2}
        error1 = [mapping[i] for i in error1]
        error2 = [mapping[i] for i in error2]
        

        error1 = np.array(error1)
        error2 = np.array(error2)
        num_different = np.sum(error1 != error2)
        kappa_score = compute_kappa_score(error1, error2)
        kappa_result[mutant] = kappa_score
    # write to file
    write_json(kappa_result, f"{output_folder}/kappa_score.json")




