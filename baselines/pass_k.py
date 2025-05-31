import json
import ast
from typing import List, Union
import numpy as np
import itertools
from tqdm import tqdm

import os
import shutil
import signal
import resource
import sys
import contextlib
import io

rmtree = shutil.rmtree
rmdir = os.rmdir
chdir = os.chdir




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




# def reliability_guard( max_memory=128 * 1024 * 1024):

#     resource.setrlimit(resource.RLIMIT_AS, (max_memory, max_memory))

#     sys.setrecursionlimit(1000)

# Disable functionalities that can make destructive changes to the test.
# reliability_guard()


def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f]
    
    

def write_jsonl(file_path, lst):
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in lst:
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + '\n')

def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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

def filter_code(completion: str, func_name: str) -> str:
    """
    Extract the first function definition from the generated code.

    Args:
        completion (str): The generated code as a string.

    Returns:
        str: The source code of the first function, or an empty string if none is found.
    """
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
    completion_lst = completion.split("\n\n")
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
    return "\n\n".join(result)


    
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


def has_return(func_code: str) -> bool:
    
    try:
        tree = ast.parse(func_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Return):
                return True
        return False
    except SyntaxError:
        return False  

if __name__ == '__main__':

    # output_path = "./results/bigcodebench/codegen2b_passat1"

    datasets = ["humaneval", "mbpp"]
    models = ["passat10_incoder-1B", "passat10_codegen-2B", "passat10_codegen2-1B", "passat10_santacoder"]
    mutant_types = ["base", "insert_line", "comment", "output_mutation", "output_v_mutation"]
    # datasets = ["mbpp"]
    # models = ["passat10_santacoder"]
    # mutant_types = ["output_v_mutation"]

    metric_result = dict()

    for k in [1, 3, 5, 7, 10]:
        pass_k_dict = dict()
        for mt_type in mutant_types:
            mutant_type_dict = dict()
            for dataset in datasets:
                dataset_dict = dict()
                for model in models:

                    output_path = f"./results/{dataset}_{mt_type}/{model}/run_results"
                    input = read_jsonl(f"{output_path}/run_results.jsonl")
                    c_lst = []
                    n = -1
                    for i in range(len(input)):
                        item = input[i]
                        if n == -1:
                            n = len(item)
                        c = item.count("passed")
                        c_lst.append(c)
                    c_arr = np.array(c_lst)
                    pass_at_k = estimate_pass_at_k(n, c_arr, k)
                    pass_at_k_avg = np.mean(pass_at_k)
                    write_text(output_path + f"/pass_at_{k}.txt", f"pass@{k}: {pass_at_k_avg}, pass@{k} list: {pass_at_k.tolist()}")
                    result_json = {
                        "pass@k": pass_at_k_avg,
                        "pass@k_list": pass_at_k.tolist()
                    }
                    write_json(output_path + f"/pass_at_{k}.json", result_json)
                    dataset_dict[model] = pass_at_k_avg
                mutant_type_dict[dataset] = dataset_dict
            pass_k_dict[mt_type] = mutant_type_dict
        metric_result[f"pass@{k}"] = pass_k_dict
    write_json(f"./results/pass_k_statistics_baselines.json", metric_result)
                
            # output_path = f"./results/{dataset}/{model}/run_results"
            # mt_types = ["mt_1", "mt_2", "mt_3"]
            # for mt_type in mt_types:
            #     input = read_jsonl(f"{output_path}/{mt_type}_item_run_results_no_return_filtered.jsonl")
                
            #     k = 1
            #     n = -1
            #     c_lst = []

            #     for i in range(len(input)):
            #         item = input[i]

            #         if n == -1:
            #             n = len(item)
            #         c = 0
            #         for j in range(len(item)):
            #             # if each result in item[j] is passed, increase c by 1
            #             passed = False
            #             for result in item[j]:
            #                 if result == "passed":
            #                     passed = True
            #                     break
            #             if passed:
            #                 c += 1
            #             # if "passed" in item[j]:
            #             #     c += 1
                        
                    
            #         c_lst.append(c)
            #     c_arr = np.array(c_lst)
            #     pass_at_k = estimate_pass_at_k(n, c_arr, k)
            #     pass_at_k_avg = np.mean(pass_at_k)

            #     write_text(output_path + f"/{mt_type}_pass_at_{k}_no_return_filtered.txt", f"pass@{k}: {pass_at_k_avg}, pass@{k} list: {pass_at_k.tolist()}")
        


