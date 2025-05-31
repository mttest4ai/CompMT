import json
import csv

def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=3)

if __name__ == "__main__":
    input_folder = "./results/manual_result"
    datasets = ["manual_humaneval", "manual_mbpp"]
    mutants = ["mutant_1", "mutant_2", "mutant_3"]
    result = dict()
    for dataset in datasets:
        result[dataset] = dict()
        for mutant in mutants:
            data = read_json(f"{input_folder}/{dataset}/{mutant}_conflict_solved.json")
            final_scores = [item["final_result"] for item in data.values()]
            avg_score = sum(final_scores) / len(final_scores)
            result[dataset][mutant] = avg_score
    write_json(result, f"{input_folder}/avg_scores.json")
    # Write the results to a CSV file
    kappa_scores = read_json(f"{input_folder}/kappa_score.json")
    csv_file_path = f"{input_folder}/avg_scores.csv"
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        # Write the header
        writer.writerow(["Dataset", "mutant1", "mutant2", "mutant3"])
        # Write the data
        for dataset in datasets:
            row = dict()
            row["Dataset"] = dataset
            row["mutant1"] = f"{result[dataset]['mutant_1']:.2f}"
            row["mutant2"] = f"{result[dataset]['mutant_2']:.2f}"
            row["mutant3"] = f"{result[dataset]['mutant_3']:.2f}"
            writer.writerow(row.values())
        # Write the kappa scores to the CSV file
        row = dict()
        row["Dataset"] = "kappa_scores"
        row["mutant1"] = f"{kappa_scores['mutant_1']:.2f}"
        row["mutant2"] = f"{kappa_scores['mutant_2']:.2f}"
        row["mutant3"] = f"{kappa_scores['mutant_3']:.2f}"
        writer.writerow(row.values())



        
            
