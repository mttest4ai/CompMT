# from code_gen import generate_codegen
# from incoder import incoder_gen
# from santacoder import santa_gen
import json
import argparse
import logging
from tqdm import tqdm
import os
from typing import List, Union
import numpy as np
import itertools
import torch
from model import make_model, generate_codes

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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

# def generate(text, model_name):
#     # if model_name == "codegen-2B":
#         # return generate_codegen(text)
#     # if model_name == "incoder-1B":
#     #     return incoder_gen(text)
#     if model_name == "santacoder":
#         return santa_gen(text)
#     else:
#         raise ValueError(f"Model {model_name} not found")

def estimate_pass_at_k(
    num_samples: Union[int, List[int], np.ndarray],
    num_correct: Union[List[int], np.ndarray],
    k: int,
) -> np.ndarray:
    """
    Estimates pass@k of each problem and returns them in an array.
    """
 
    def estimator(n: int, c: int, k: int) -> float:
        """
        Calculates 1 - comb(n - c, k) / comb(n, k).
        """
        if n - c < k:
            return 1.0
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))
 
    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)
 
    return np.array(
        [estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)]
    )

def code_generate(mutant_path, model_name, output_path, dataset, n_samples=1):
    # set logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(output_path+"/mutant_generate.log")
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Start to initialize mutants")


    # read mutant
    results = read_jsonl(mutant_path)
    if dataset == "humaneval":
        results.sort(key=lambda x: int(x["task_id"].split("_")[-1]))

    model = make_model(model_name)
    logger.info("Start to generate mutants")
    generate_results = []
    
    if not os.path.exists(output_path+"/mutant_results_generate.jsonl"):
        write_jsonl(output_path+"/mutant_results_generate.jsonl", generate_results)
    else:
        generate_results = read_jsonl(output_path+"/mutant_results_generate.jsonl")
    
    

    finished_task_ids = [task["task_id"] for task in generate_results]
    if os.path.exists(output_path+"/prompt_to_sample_codes.json"):
        prompt_to_sample_codes = read_json(output_path+"/prompt_to_sample_codes.json")
    else:
        prompt_to_sample_codes = dict()
    for task in tqdm(results):
        if task["task_id"] in finished_task_ids:
            continue
        
        prompt = task["prompt"]
        if prompt in prompt_to_sample_codes:
            task["sample_codes"] = prompt_to_sample_codes[prompt]
        else:
            codes = generate_codes(model, prompt, n_samples)
            task["sample_codes"] = codes
            prompt_to_sample_codes[prompt] = codes
        generate_results.append(task)
        write_jsonl(output_path+"/mutant_results_generate.jsonl", generate_results)
        write_json(output_path+"/prompt_to_sample_codes.json",prompt_to_sample_codes)
        # for i in range(n_samples):
        #     prompt = task["prompt"]
        #     if prompt not in prompt_to_sample_codes:
        #         prompt_to_sample_codes[prompt] = []
        #     else:
        #         if len(prompt_to_sample_codes[prompt]) >= n_samples:
        #             break
        #     code = generate(prompt, model_name)
        #     prompt_to_sample_codes[prompt].append(code)
        # task["sample_codes"] = prompt_to_sample_codes[prompt]
        # generate_results.append(task)



        
        # write_jsonl(output_path+"/mutant_results_generate.jsonl", generate_results)
        # write_json(output_path+"/prompt_to_sample_codes.json",prompt_to_sample_codes)
    logger.info("Generate mutants finishs.")
        
    



if __name__ == '__main__':
    # dataset = "humaneval"
    # mutant_type="output_mutation"
    # mutant_path = f"../../baselines/datasets/{dataset}/{mutant_type}/{dataset}_{mutant_type}.jsonl"
    # # model_name = "codegen2-1B_P"
    # model_name = "incoder-1B"
    # n_samples = 1
    # output_path = f"../../baselines/results/{dataset}_{mutant_type}/passat{n_samples}_{model_name}"
    # if not os.path.exists(output_path):
    #     os.makedirs(output_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str)
    parser.add_argument('--mutant_path', type=str)
    parser.add_argument('--model_name', type=str)
    parser.add_argument('--output_path', type=str)
    parser.add_argument('--n_samples', type=int, default=1)

    args = parser.parse_args()

    mutant_path = args.mutant_path
    model_name = args.model_name
    output_path = args.output_path
    n_samples = args.n_samples
    dataset = args.dataset

    code_generate(mutant_path, model_name, output_path, dataset, n_samples)
