import json
import ast
from typing import List, Union
import numpy as np
import itertools
from tqdm import tqdm
import random
import os
import shutil
import signal
import resource
import sys
import contextlib
import logging
import io
import argparse
import time
import re
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

rmtree = shutil.rmtree
rmdir = os.rmdir
chdir = os.chdir

NON_CODE_EOS = ["<|endoftext|>", "\n```", "\n</s>", "<|endofmask|>"]


class TimeoutException(Exception):
    pass


class WriteOnlyStringIO(io.StringIO):
    """ StringIO that throws an exception when it's read from """

    def read(self, *args, **kwargs):
        raise IOError

    def readline(self, *args, **kwargs):
        raise IOError

    def readlines(self, *args, **kwargs):
        raise IOError

    def readable(self, *args, **kwargs):
        """ Returns True if the IO object can be read. """
        return False


class redirect_stdin(contextlib._RedirectStream):  # type: ignore
    _stream = 'stdin'


@contextlib.contextmanager
def time_limit(seconds: float):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.setitimer(signal.ITIMER_REAL, seconds)
    signal.signal(signal.SIGALRM, signal_handler)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@contextlib.contextmanager
def swallow_io():
    stream = WriteOnlyStringIO()
    with contextlib.redirect_stdout(stream):
        with contextlib.redirect_stderr(stream):
            with redirect_stdin(stream):
                yield

def random_sample(lst, k, seed=2345):
    random.seed(seed)
    k = min(k, len(lst))
    indices = random.sample(range(len(lst)), k)  
    samples = [lst[i] for i in indices]  
    return samples, indices


def reliability_guard( max_memory=8 * 1024 * 1024 * 1024):

    resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))

    sys.setrecursionlimit(1000)

# Disable functionalities that can make destructive changes to the test.
reliability_guard()

def read_json(file_path: str):
    with open(file_path, 'r', encoding="utf-8") as file:
        data = json.load(file)
    return data

def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f]
    
    

def write_jsonl(file_path, lst):
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in lst:
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + '\n')

def write_text(file_path, text):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)

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

def extract_func(code):
    try:
        # Parse the code into an AST
        result_lines = []
        tree = ast.parse(code)
        for node in tree.body:
            # Check if the node is a function definition
            if isinstance(node, ast.FunctionDef):
                # Extract the function code
                return '\n'.join(result_lines) + '\n' + ast.get_source_segment(code, node)
            else:
                result_lines.append(ast.get_source_segment(code, node))
    except Exception as e:
        return code
    
def truncate_by_eos(code: str, eos: List) -> str:
    min_index = len(code)
    for e in eos:
        index = code.find(e)
        if 0 <= index < min_index:
            min_index = index
    return code[:min_index]


def filter_code(completion: str, func_name: str, eos: List) -> str:
    """
    Extract the first function definition from the generated code.

    Args:
        completion (str): The generated code as a string.
        eos (List): The list of end-of-string tokens to split the code on.

    Returns:
        str: The source code of the first function, or an empty string if none is found.
    """
    completion = truncate_by_eos(completion, eos)
    
    try:
        # Parse the code into an AST
        result_lines = []
        tree = ast.parse(completion)
        for node in tree.body:
            # Check if the node is a function definition
            if isinstance(node, ast.FunctionDef):
                # Extract the function code
                return '\n'.join(result_lines) + '\n' + ast.get_source_segment(completion, node)
            else:
                result_lines.append(ast.get_source_segment(completion, node))
    except Exception as e:
        pass 
    completion = completion.lstrip("\n")
    completion_lst = re.split(r'\n(?=def )', completion)
    contain_flag = 0
    result = []
    for code in completion_lst:
        # collect def func_name and code before it
        if code.strip() == "":
            continue
        if contain_flag == 0:
            if f"def {func_name}" in code:
                contain_flag = 1
            result.append(code)
        else:
            break
    code_result =  "\n".join(result)
    code_result = extract_func(code_result)
    return code_result


    
def extract_test_inputs(assert_code: str) -> list:
    tree = ast.parse(assert_code)
    test_cases = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert): 

            if isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.Call):
                func_call = node.test.left 
                func_name = func_call.func.id 
                args = [ast.literal_eval(arg) for arg in func_call.args] 
                test_cases.append((func_name, args))  

    return test_cases

def get_check_program(seed_code, comb_code, mutant_code, mt_assert_list):
    check_program = (
        seed_code + "\n\n" + comb_code + "\n\n" + mutant_code + "\n\n" + "\n".join(mt_assert_list)
    )
    return check_program

def get_sample_run_results(check_program):
    sample_run_result = ""
    try:
        exec_globals = {}
        with swallow_io():
            with time_limit(30):
                exec(check_program, exec_globals)
        sample_run_result = "passed"
    except TimeoutException:
        sample_run_result = "timed out"
    except BaseException as e:
        if str(e) == "":
            error_type = e.__class__.__name__
            sample_run_result = f"failed: {error_type}"
        else:
            sample_run_result = f"failed: {e}"
    return sample_run_result

def has_return(func_code: str) -> bool:
    
    try:
        tree = ast.parse(func_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Return):
                return True
        return False
    except SyntaxError:
        return False  
    
def write_py_codes(py_codes, folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
    for i, code in enumerate(py_codes):
        with open(f"{folder}/{i}.py", "w") as f:
            f.write(code)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str)
    parser.add_argument('--dataset', type=str)
    parser.add_argument('--model', type=str)

    args = parser.parse_args()

    output_path = args.output_path
    dataset = args.dataset
    model = args.model




    # dataset = "human-eval"
    # # dataset = "mbpp-sanitized_oneshot"
    # model = "santacoder"
    # output_path = f"../results/init_{dataset}_vner4v1/passat10_{model}"
    # # task_id_to_test_path = f"../results/init_{dataset}_vner4/task_id_to_test.json"
    
    
    

    input_data = read_jsonl(f"{output_path}/mutant_results_generate.jsonl")
    if not os.path.exists(output_path+"/run_results"):
        os.makedirs(output_path+"/run_results")

    # set logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(output_path+"/run_results/evaluate.log")
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Start to evaluate.")

    
    
    k = 10

    if os.path.exists(output_path + "/run_results" + "/mutant_results_run.jsonl"):
        result_jsonl = read_jsonl(output_path + "/run_results" + "/mutant_results_run.jsonl")
        mt_1_item_run_results = read_jsonl(output_path + "/run_results" + "/mt_1_item_run_results.jsonl")
        mt_2_item_run_results = read_jsonl(output_path + "/run_results" + "/mt_2_item_run_results.jsonl")
        mt_3_item_run_results = read_jsonl(output_path + "/run_results" + "/mt_3_item_run_results.jsonl")
    else:
        result_jsonl = []
        mt_1_item_run_results = []
        mt_2_item_run_results = []
        mt_3_item_run_results = []
    func_pass_but_no_return = []
    continue_point = len(result_jsonl)
    # continue_point = 84
    begin_point = continue_point
    count = continue_point
    
    if continue_point == 0:
        continue_point = -1
    progress_bar = tqdm(total=len(input_data), desc="Processing items", initial=count)

    for item in input_data[begin_point::]:
        # if count == 128:
        #     print(128)
        
        seed_name = item["entry_point"]
        task_id = item["task_id"]
        test_list = item["test_asserts"]
        test_rand_num = len(test_list)
        if "mutant_1_item" in item:
            mutant_item = item["mutant_1_item"]
            item_mt_1_check_programs = []
            item_mt_1_run_results = []
            mt_assert_list = mutant_item['mt_assert_list']
            sampled_mt_assert_list, sampled_mt_assert_list_ids = random_sample(mt_assert_list, test_rand_num, 1234)
            
            for j in range(k):
                sample_result = mutant_item["sample_results"][j]
                seed_code = sample_result["seed_code"]
                comb_code = sample_result["comb_code"]
                mutant_code = sample_result["mutant_code"]
                check_program = get_check_program(seed_code, comb_code, mutant_code, sampled_mt_assert_list)
                
                
                if count == continue_point:
                    sample_run_result = "failed: manual break"
                else:
                    sample_run_result = get_sample_run_results(check_program)

                if sample_run_result == "passed":
                    if (not has_return(seed_code)) or (not has_return(comb_code)) or (not has_return(mutant_code)):
                        sample_run_result = "failed: no return"
                        func_pass_but_no_return.append(check_program)
                        write_py_codes(func_pass_but_no_return, output_path + "/run_results" + "/func_pass_but_no_return")


                item_mt_1_check_programs.append(check_program)
                item_mt_1_run_results.append(sample_run_result)
            mt_1_item_run_results.append(item_mt_1_run_results)
            mutant_item["sampled_mt_assert_list"] = sampled_mt_assert_list
            mutant_item["sampled_mt_assert_list_ids"] = sampled_mt_assert_list_ids
            mutant_item["check_programs"] = item_mt_1_check_programs
            mutant_item["run_results"] = item_mt_1_run_results


            item["mutant_1_item"] = mutant_item
            item["mutant_1_item_run_results"] = item_mt_1_run_results

        if "mutant_2_item" in item:
            mutant_item = item["mutant_2_item"]
            item_mt_2_check_programs = []
            item_mt_2_run_results = []
            mt_assert_list = mutant_item['mt_assert_list']
            sampled_mt_assert_list, sampled_mt_assert_list_ids = random_sample(mt_assert_list, test_rand_num, 1234)
            for j in range(k):

                sample_result = mutant_item["sample_results"][j]
                seed_code = sample_result["seed_code"]
                comb_code = sample_result["comb_code"]
                mutant_code = sample_result["mutant_code"]
                check_program = get_check_program(seed_code, comb_code, mutant_code, sampled_mt_assert_list)

                if count == continue_point:
                    sample_run_result = "failed: manual break"
                else:
                    sample_run_result = get_sample_run_results(check_program)

                if sample_run_result == "passed":
                    if (not has_return(seed_code)) or (not has_return(comb_code)) or (not has_return(mutant_code)):
                        sample_run_result = "failed: no return"
                        func_pass_but_no_return.append(check_program)
                        write_py_codes(func_pass_but_no_return, output_path + "/run_results" + "/func_pass_but_no_return")

                item_mt_2_check_programs.append(check_program)
                item_mt_2_run_results.append(sample_run_result)
            mt_2_item_run_results.append(item_mt_2_run_results)
            mutant_item["sampled_mt_assert_list"] = sampled_mt_assert_list
            mutant_item["sampled_mt_assert_list_ids"] = sampled_mt_assert_list_ids
            mutant_item["check_programs"] = item_mt_2_check_programs
            mutant_item["run_results"] = item_mt_2_run_results
            item["mutant_2_item"] = mutant_item
            item["mutant_2_item_run_results"] = item_mt_2_run_results

        if "mutant_3_item" in item:
            mutant_item = item["mutant_3_item"]
            item_mt_3_run_results = []
            item_mt_3_check_programs = []
            mt_assert_list = mutant_item['mt_assert_list']
            sampled_mt_assert_list, sampled_mt_assert_list_ids = random_sample(mt_assert_list, test_rand_num, 1234)
            
            for j in range(k):

                # for mutant_item in mutant_items:

                sample_result = mutant_item["sample_results"][j]
                seed_code = sample_result["seed_code"]
                comb_codes = sample_result["comb_codes"]
                comb_code = "\n\n".join(comb_codes)
                mutant_code = sample_result["mutant_code"]
                check_program = get_check_program(seed_code, comb_code, mutant_code, sampled_mt_assert_list)

                if count == continue_point:
                    sample_run_result = "failed: manual break"
                else:
                    sample_run_result = get_sample_run_results(check_program)

                if sample_run_result == "passed":
                    if (not has_return(seed_code)) or (not has_return(comb_code)) or (not has_return(mutant_code)):
                        sample_run_result = "failed: no return"
                        func_pass_but_no_return.append(check_program)
                        write_py_codes(func_pass_but_no_return, output_path + "/run_results" + "/func_pass_but_no_return")

                item_mt_3_check_programs.append(check_program)
                item_mt_3_run_results.append(sample_run_result)
            mt_3_item_run_results.append(item_mt_3_run_results)
            mutant_item["sampled_mt_assert_list"] = sampled_mt_assert_list
            mutant_item["sampled_mt_assert_list_ids"] = sampled_mt_assert_list_ids
            mutant_item["check_programs"] = item_mt_3_check_programs
            mutant_item["run_results"] = item_mt_3_run_results
            item["mutant_3_item"] = mutant_item
            item["mutant_3_item_run_results"] = item_mt_3_run_results
        result_jsonl.append(item)


        write_jsonl(output_path + "/run_results" + "/mutant_results_run.jsonl", result_jsonl)
        write_jsonl(output_path + "/run_results" + "/mt_1_item_run_results.jsonl", mt_1_item_run_results)
        write_jsonl(output_path + "/run_results" + "/mt_2_item_run_results.jsonl", mt_2_item_run_results)
        write_jsonl(output_path + "/run_results" + "/mt_3_item_run_results.jsonl", mt_3_item_run_results)
        count+=1
        progress_bar.update(1)
    progress_bar.close()
    logger.info("Evaluation Finished")
        


