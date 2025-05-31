import json


def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f]
    

def statistics_result(result_list):
    result_task_passed_ids = []
    result_task_not_passed_ids = []
    for item in result_list:
        task_id = item["task_id"]
        run_results = item["run_results"]
        if "passed" in run_results:
            result_task_passed_ids.append(task_id)
        else:
            result_task_not_passed_ids.append(task_id)
    return {"passed": result_task_passed_ids, "not_passed": result_task_not_passed_ids}


def main():
    datasets = ["humaneval", "mbpp"]
    models = ["passat10_codegen-2B", "passat10_codegen2-1B", "passat10_incoder-1B", "passat10_santacoder"]
    mutant_types = ["base", "comment", "insert_line", "output_mutation", "output_v_mutation"]
    for dataset in datasets:
        result_dict = {}
        for model in models:
            model_result_dict = {}
            for mutant_type in mutant_types:
                result_path = f"./results/{dataset}_{mutant_type}/{model}/run_results/mutant_results_run.jsonl"
                result_list = read_jsonl(result_path)
                result_task_ids = statistics_result(result_list)
                model_result_dict[mutant_type] = result_task_ids
            result_dict[model] = model_result_dict
        if dataset == "humaneval":
            write_json(f"./results/{dataset}_statistics_result.json", result_dict)
        elif dataset == "mbpp":
            write_json(f"./results/mbpp-sanitized_statistics_result.json", result_dict)


if __name__ == '__main__':
    main()