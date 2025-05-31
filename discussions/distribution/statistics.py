import json


def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f]
    
    

def write_jsonl(file_path, lst):
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in lst:
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + '\n')

def read_json(file_path: str):
    with open(file_path, 'r', encoding="utf-8") as file:
        data = json.load(file)
    return data

def write_json(file_path: str, data):
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    datasets = ["init_human-eval_vner4", "init_mbpp-sanitized_vner4"]
    models = ["passat10_codegen-2B", "passat10_codegen2-1B", "passat10_incoder-1B", "passat10_santacoder"]
    mt_types = ["mt_1", "mt_2", "mt_3"]
    mt_types_to_keyname = {"mt_1": "mutant_1", "mt_2": "mutant_2", "mt_3": "mutant_3"}
    evaluate_path = "../../evaluate/results"
    result = dict()
    for mutant in ["mutant_1", "mutant_2", "mutant_3"]:
        result[mutant] = dict()
        for pass_num in range(1, 11):
            result[mutant][pass_num] = 0
    for dataset in datasets:

        for model in models:
            for mt_type in mt_types:
                input_path = f"{evaluate_path}/{dataset}/{model}/run_results/{mt_type}_item_run_results.jsonl"
                input = read_jsonl(input_path)
                mutant_type = mt_types_to_keyname[mt_type]
                for i in range(len(input)):
                    item = input[i]
                    c = item.count("passed")
                    if c > 0:
                        result[mutant_type][c] += 1
    write_json(f"./combmt_pass_num_statistics.json", result)

    baseline_result = dict()
    baselines = ["base", "comment", "insert_line", "output_mutation", "output_v_mutation"]
    for baseline in baselines:
        baseline_result[baseline] = dict()
        for pass_num in range(1, 11):
            baseline_result[baseline][pass_num] = 0
    baselines_path = "../../baselines/results"
    for dataset in ["humaneval", "mbpp"]:
        for baseline in baselines:
            for model in models:
                input_path = f"{baselines_path}/{dataset}_{baseline}/{model}/run_results/run_results.jsonl"
                input = read_jsonl(input_path)
                for i in range(len(input)):
                    item = input[i]
                    c = item.count("passed")
                    if c > 0:
                        baseline_result[baseline][c] += 1
    write_json(f"./baseline_pass_num_statistics.json", baseline_result)










