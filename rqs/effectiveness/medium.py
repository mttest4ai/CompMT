import numpy as np
import json
import csv

def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_medium(lst):
    """
    Get the medium value from a list of numbers.
    """
    if len(lst) == 0:
        return 0
    lst.sort()
    n = len(lst)
    if n % 2 == 0:
        return (lst[n // 2 - 1] + lst[n // 2]) / 2
    else:
        return lst[n // 2]


def main():
    combmt_data = read_json("./dataset/pass_k_statistics_combmt.json")
    baselines_data = read_json("./dataset/pass_k_statistics_baselines.json")
    combmt_mutants = ["mutant_1", "mutant_2", "mutant_3"]
    baselines = ["base", "insert_line", "comment", "output_mutation", "output_v_mutation"]
    stats_results = {}
    models = ["passat10_incoder-1B", "passat10_codegen-2B", "passat10_codegen2-1B", "passat10_santacoder"]
    datasets = ["humaneval", "mbpp"]
    metrics = ["pass@1", "pass@3", "pass@5", "pass@7", "pass@10"]
    sort_results = {}

    for metric in metrics:
        stats_results[metric] = []
        sort_results[metric] = []
        for baseline in baselines:
            baseline_result = dict()
            results_under_metric = []
            for dataset in datasets:
                for model in models:
                    result_of_baseline = baselines_data[metric][baseline][dataset][model]
                    results_under_metric.append(result_of_baseline)
            baseline_result["method"] = baseline
            baseline_result["results"] = results_under_metric
            baseline_result["medium"] = get_medium(results_under_metric)
            stats_results[metric].append(baseline_result)
        for mutant in combmt_mutants:
            mutant_result = dict()
            results_under_metric = []
            for dataset in datasets:
                for model in models:
                    result_of_mutant = combmt_data[metric][mutant][dataset][model]
                    results_under_metric.append(result_of_mutant)
            mutant_result["method"] = mutant
            mutant_result["results"] = results_under_metric
            mutant_result["medium"] = get_medium(results_under_metric)
            stats_results[metric].append(mutant_result)
        stats_results[metric].sort(key=lambda x: x["medium"])
        for baseline in stats_results[metric]:
            sort_results[metric].append(baseline["method"])
    write_json("./results/pass_k_statistics_combmt_medium.json", stats_results)
    write_json("./results/pass_k_statistics_combmt_medium_sort.json", sort_results)
if __name__ == "__main__":
    main()