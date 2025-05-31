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
import random
from model import make_model, generate_code, generate_codes


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

def random_sample(lst, k, seed=2345):
    random.seed(seed)
    k = min(k, len(lst))
    indices = random.sample(range(len(lst)), k)  
    samples = [lst[i] for i in indices]  
    return samples, indices

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

class MyFilter(logging.Filter):
    def filter(self, record):
        if "openai" in record.getMessage():
            return False
        return True

def code_generate(mutant_path, model_name, output_path, n_samples=1):
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
    model = make_model(model_name)

    logger.info("Start to generate mutants")
    generate_results = []
    
    if not os.path.exists(output_path+"/mutant_results_generate.jsonl"):
        write_jsonl(output_path+"/mutant_results_generate.jsonl", generate_results)
    else:
        generate_results = read_jsonl(output_path+"/mutant_results_generate.jsonl")
    
    

    finished_task_ids = [task["task_id"] for task in generate_results]

    prompt_to_sample_codes = dict()
    for task in tqdm(results):
        if task["task_id"] in finished_task_ids:
            continue

        mutant_1_flag = False
        mutant_2_flag = False
        mutant_3_flag = False
        
        if "mutant_1_item" in task:
            mutant_1_item = task["mutant_1_item"]
            mutant_1_flag = True
            
        if "mutant_2_item" in task:
            mutant_2_item = task["mutant_2_item"]
            mutant_2_flag = True
        
        if "mutant_3_item" in task:
            mutant_3_item = task["mutant_3_item"]
            mutant_3_flag = True



        for i in range(n_samples):
            # mutant_1
            # for mutant_1_item in task["mutant_1"]:
            if mutant_1_flag:
                if "sample_results" not in mutant_1_item:
                    mutant_1_item["sample_results"] = []

                seed_task_prompt = task["prompt"] 
                comb_task_prompt = mutant_1_item["comb_task_prompt"]
                mutant_prompt = mutant_1_item["mutant_prompt"]

                if seed_task_prompt not in prompt_to_sample_codes:
                    prompt_to_sample_codes[seed_task_prompt] = []
                seed_code = generate_code(model, seed_task_prompt)
                prompt_to_sample_codes[seed_task_prompt].append(seed_code)


                if comb_task_prompt not in prompt_to_sample_codes:
                    prompt_to_sample_codes[comb_task_prompt] = []
                comb_code = generate_code(model, comb_task_prompt)
                prompt_to_sample_codes[comb_task_prompt].append(comb_code)
                
                if mutant_prompt not in prompt_to_sample_codes:
                    prompt_to_sample_codes[mutant_prompt]=[]
                mutant_code = generate_code(model, mutant_prompt)
                prompt_to_sample_codes[mutant_prompt].append(mutant_code)
                mutant_1_item["sample_results"].append({"seed_code": seed_code, "comb_code": comb_code, "mutant_code": mutant_code})


            # mutant_2
            # for mutant_2_item in task["mutant_2"]:
            if mutant_2_flag:
                if "sample_results" not in mutant_2_item:
                    mutant_2_item["sample_results"] = []

                seed_task_prompt = task["prompt"]
                comb_task_prompt = mutant_2_item["comb_task_prompt"]
                mutant_prompt = mutant_2_item["mutant_prompt"]

                if seed_task_prompt not in prompt_to_sample_codes:
                    prompt_to_sample_codes[seed_task_prompt] = []
                seed_code = generate_code(model, seed_task_prompt)
                prompt_to_sample_codes[seed_task_prompt].append(seed_code)

                if comb_task_prompt not in prompt_to_sample_codes:
                    prompt_to_sample_codes[comb_task_prompt] = []
                comb_code = generate_code(model, comb_task_prompt)
                prompt_to_sample_codes[comb_task_prompt].append(comb_code)

                mutant_code = generate_code(model, mutant_prompt)
                if mutant_prompt not in prompt_to_sample_codes:
                    prompt_to_sample_codes[mutant_prompt]=[]
                prompt_to_sample_codes[mutant_prompt].append(mutant_code)
                mutant_2_item["sample_results"].append({"seed_code": seed_code, "comb_code": comb_code, "mutant_code": mutant_code})


            # mutant_3
            # for mutant_3_item in task["mutant_3"]:
            if mutant_3_flag:
                if "sample_results" not in mutant_3_item:
                    mutant_3_item["sample_results"] = []

                seed_task_prompt = task["prompt"]
                comb_task_prompts = mutant_3_item["comb_task_prompts"]
                mutant_prompt = mutant_3_item["mutant_prompt"]

                if seed_task_prompt not in prompt_to_sample_codes:
                    prompt_to_sample_codes[seed_task_prompt] = []
                seed_code = generate_code(model, seed_task_prompt)
                prompt_to_sample_codes[seed_task_prompt].append(seed_code)
                
                comb_codes = []
                for comb_task_prompt in comb_task_prompts:

                    comb_code = generate_code(model, comb_task_prompt)
                    comb_codes.append(comb_code)
                    if comb_task_prompt not in prompt_to_sample_codes:
                        prompt_to_sample_codes[comb_task_prompt] = []
                    prompt_to_sample_codes[comb_task_prompt].append(comb_code)
                mutant_code = generate_code(model, mutant_prompt)
                if mutant_prompt not in prompt_to_sample_codes:
                    prompt_to_sample_codes[mutant_prompt]=[]
                prompt_to_sample_codes[mutant_prompt].append(mutant_code)
                mutant_3_item["sample_results"].append({"seed_code": seed_code, "comb_codes": comb_codes, "mutant_code": mutant_code})
            if model_name == "chatgpt":
                logger.info(f"ChatGPT generate sample {i+1} for task {task['task_id']}")

        if mutant_1_flag:
            task["mutant_1_item"] = mutant_1_item
        if mutant_2_flag:
            task["mutant_2_item"] = mutant_2_item
        if mutant_3_flag:
            task["mutant_3_item"] = mutant_3_item
        generate_results.append(task)


        
        write_jsonl(output_path+"/mutant_results_generate.jsonl", generate_results)
        write_json(output_path+"/prompt_to_sample_codes.json",prompt_to_sample_codes)
    logger.info("Generate mutants finishs.")
        
    



if __name__ == '__main__':
    # dir_name = "init_human-eval_vner4"
    # mutant_path = f"../../mutant/results/{dir_name}/mutant_results_init.jsonl"
    # # model_name = "codegen2-1B_P"
    # model_name = "chatgpt"
    # n_samples = 1
    # output_path = f"../../mutant/results/{dir_name}/passat{n_samples}_{model_name}"
    # if not os.path.exists(output_path):
    #     os.makedirs(output_path)

    parser = argparse.ArgumentParser()
    parser.add_argument('--mutant_path', type=str)
    parser.add_argument('--model_name', type=str)
    parser.add_argument('--output_path', type=str)
    parser.add_argument('--n_samples', type=int, default=1)

    args = parser.parse_args()

    mutant_path = args.mutant_path
    model_name = args.model_name
    output_path = args.output_path
    n_samples = args.n_samples

    code_generate(mutant_path, model_name, output_path, n_samples)
