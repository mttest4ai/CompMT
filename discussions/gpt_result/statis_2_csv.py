import json
import csv

def read_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)
    
pass_k_statistics = read_json("./pass_k_statistics_combmt.json")

with open("./pass_k_statistics_combmt.csv", mode='w', newline='', encoding='utf-8-sig') as file:
    fieldnames = ["Dataset", "MR"]+ ["Pass@1", "Pass@3", "Pass@5", "Pass@7", "Pass@10"]
    datasets = ["HumanEval", "MBPP"]
    dataset_to_keyname = {"HumanEval": "humaneval", "MBPP": "mbpp"}
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for dataset in datasets:
        for mt_id in range(1, 4):
            row = {"Dataset": dataset, "MR": f"MR{mt_id}"}
            for k in [1, 3, 5, 7, 10]:
                pass_k = pass_k_statistics[f"pass@{k}"][f"mutant_{mt_id}"][dataset_to_keyname[dataset]]["passat10_chatgpt"]
                row[f"Pass@{k}"] = pass_k
            writer.writerow(row)
            