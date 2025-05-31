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

# def get_sample_run_results(seed_code, comb_code, mutant_code, mt_assert_list):
#     sample_run_result = ""
#     check_program = (
#         seed_code + "\n\n" + comb_code + "\n\n" + mutant_code + "\n\n" + "\n".join(mt_assert_list)
#     )
#     try:
#         exec_globals = {}
#         with swallow_io():
#             with time_limit(30):
#                 exec(check_program, exec_globals)
#         sample_run_result = "passed"
#     except TimeoutException:
#         sample_run_result = "timed out"
#     except BaseException as e:
#         sample_run_result = f"failed: {e}"
#     return sample_run_result

def get_sample_run_result(code, test_code):
    sample_run_result = ""
    check_program = (
        code + "\n\n" + test_code
    )
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


def extract_method_name(task_id: str, name: str) -> str:
    return name[len(task_id) + 1:]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_path', type=str)
    parser.add_argument('--dataset', type=str)
    parser.add_argument('--model', type=str)
    parser.add_argument('--mutant_type', type=str)

    args = parser.parse_args()

    output_path = args.output_path
    dataset = args.dataset
    model = args.model
    mutant_type = args.mutant_type




    # dataset = "humaneval"
    # # dataset = "mbpp-sanitized_oneshot"
    # mutant_type = "output_mutation"
    # model = "santacoder"
    # output_path = f"../results/{dataset}_{mutant_type}/passat10_{model}"

    eos = NON_CODE_EOS
    if model == "incoder-1B":
        extra_eos = [
            "<|endofmask|>",
            "<|/ file",
            "</cell>",
            "</text>",
            "</code>",
            "<|",
            "</CODE>",
        ]
        eos += extra_eos
    elif model == "codegen2-1B":
        extra_eos = ["<|python"]
        eos += extra_eos
    elif model == "santacoder":
        extra_eos = ["<|endoftext|>"]
        eos += extra_eos




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
        run_results = read_jsonl(output_path + "/run_results" + "/run_results.jsonl")

    else:
        result_jsonl = []
        run_results = []
    
    continue_point = len(result_jsonl)
    # continue_point = 84
    count = continue_point
    begin = continue_point
    
    if continue_point == 0:
        continue_point = -1
    progress_bar = tqdm(total=len(input_data), desc="Processing items", initial=count)

    for item in input_data[begin::]:
        task_id = item["task_id"]
        # if dataset == "humaneval":
        #     entry_point = extract_method_name(task_id, item["name"])
        # elif dataset == "mbpp-sanitized_oneshot":
        #     entry_point = item["name"]
        # else:
        #     raise ValueError(f"Unknown dataset: {dataset}")

        test_code = item["tests"]
        sample_codes = item["sample_codes"]
        item_run_results = []

        for i in range(k):
            if count == continue_point:
                item_run_results.append("failed: manual break")
                continue
            code = sample_codes[i] # filter_code(sample_codes[i], entry_point, eos)
            sample_run_result = get_sample_run_result(code, test_code)
            item_run_results.append(sample_run_result)
        run_results.append(item_run_results)
        item["run_results"] = item_run_results
        result_jsonl.append(item)
        write_jsonl(output_path + "/run_results" + "/mutant_results_run.jsonl", result_jsonl)
        write_jsonl(output_path + "/run_results" + "/run_results.jsonl", run_results)
        count+=1
        progress_bar.update(1)
    progress_bar.close()
    logger.info("Evaluation Finished")


