import json
import csv

def read_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

if __name__ == "__main__":
    # Read the JSON file
    json_file_path = "diversity.json"
    data = read_json(json_file_path)
    output_path = "diversity.csv"

    with open (output_path, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(["Methods", "BLUE_humaneval", "SemSim_humaneval", "BLEU_mbpp", "SemSim_mbpp"])
        # Write the data
        methods = data["humaneval"].keys()
        for method in methods:
            row = {}
            row["Methods"] = method
            row["BLUE_humaneval"] = "{:.2f}".format(data["humaneval"][method]["bleu"])
            row["SemSim_humaneval"] = "{:.2f}".format(data["humaneval"][method]["embedding_sim"])
            row["BLEU_mbpp"] = "{:.2f}".format(data["mbpp"][method]["bleu"])
            row["SemSim_mbpp"] = "{:.2f}".format(data["mbpp"][method]["embedding_sim"])
            writer.writerow(row.values())

            
