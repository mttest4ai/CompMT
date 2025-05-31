
from bgesimien import getSimilarity
import type_match
import ast
import astor
import copy
import json
import argparse
import logging
import prompt_gen
from tqdm import tqdm
from typing import List, Optional
import random
import os
import itertools

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def read_jsonl(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    return lines

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

def single2single():
    pass

def single2multi():
    pass

def is_subset(array1, array2):
    return set(array1).issubset(array2)

def extract_assert_statements(code):
    # get assert statements from code
    tree = ast.parse(code)  
    assert_statements = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):  
            assert_statements.append(astor.to_source(node).strip())

    return assert_statements

def extract_prompt_call_from_assert(assert_code: str) -> str:
    tree = ast.parse(assert_code)
    # Find the function call node
    call_node = next(
        node for node in ast.walk(tree) if isinstance(node, ast.Call)
    )
    # Return the source code of the function call
    return astor.to_source(call_node).strip()

def extract_code_before_function_signature(code):
    tree = ast.parse(code)
    result_lines = []
    function_name = ""
    
    for node in tree.body:
        # Check whether it is a function definition node
        if isinstance(node, ast.FunctionDef):
            # Get the source code of the function definition and add it to the result
            function_signature = f"def {node.name}("
            function_name = node.name
            args = [arg.arg for arg in node.args.args]
            function_args = args
            function_signature += ", ".join(args) + "):"
            result_lines.append(function_signature)
            break  # Stop once the first function definition is found
        else:
            # Non-function definition node, add code directly
            result_lines.append(ast.get_source_segment(code, node))

    return '\n'.join(result_lines), function_name, function_args

def extract_method_calls(prompt: str, entry_point: str) -> List[str]:
    """
    Extracts method call examples from a given prompt string, supporting nested parentheses.

    :param prompt: The input string containing function definitions and examples.
    :param entry_point: The name of the function to extract calls for.
    :return: A list of method call examples as strings.
    """
    calls = []
    i = 0
    while i < len(prompt):
        # Find the position of the method name followed by an opening parenthesis
        start_idx = prompt.find(entry_point + "(", i)
        if start_idx == -1:
            break  # No more occurrences of the method found
        
        # Use a stack to match parentheses, supporting nested ones
        stack = []
        end_idx = start_idx
        for j in range(start_idx, len(prompt)):
            char = prompt[j]
            if char == "(":
                stack.append(char)
            elif char == ")":
                stack.pop()
                if not stack:  # Stack is empty, meaning parentheses are balanced
                    end_idx = j
                    break
        
        # Extract the full method call if parentheses are balanced
        if stack:  # If the stack is not empty, parentheses are unmatched
            break
        calls.append(prompt[start_idx:end_idx + 1])
        
        # Update the search start position
        i = end_idx + 1

    return calls


def extract_docstring(prompt: str, entry_point: str) -> Optional[str]:
    """
    Extract the docstring of a specified function from a given Python prompt.

    :param prompt: The Python code as a string.
    :param entry_point: The name of the function to extract the docstring from.
    :return: The docstring of the specified function or None if not found.
    """
    try:
        # Parse the code into an abstract syntax tree (AST)
        tree = ast.parse(prompt)
        
        # Iterate over all nodes in the module body
        for node in tree.body:
            # Check if the node is a function definition and matches the entry_point
            if isinstance(node, ast.FunctionDef) and node.name == entry_point:
                # Return the docstring of the function (if it exists)
                return ast.get_docstring(node)
        return None
    except Exception as e:
        print(f"Error parsing code: {e}")
        return None

    
def filter_test_list(test_list, function_name, function_args):
    # filter test list, delete the test cases that name is not the same as function_name
    new_test_list = []
    for test in test_list:
        try:
            
            test_cases = extract_test_inputs_from_assert(test)
        except Exception as e:
            continue
        flag_has_right_call = False
        for func_name, args in test_cases:
            if func_name == function_name and len(args) == len(function_args):
                flag_has_right_call = True
                break
        if flag_has_right_call:
            new_test_list.append(test)
    return new_test_list

def extract_test_inputs_from_assert(assert_code: str) -> list:
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

def extract_test_inputs_from_statement(statement: str) -> list:

    # Parse the string into an abstract syntax tree (AST)
    tree = ast.parse(statement, mode='eval')
    
    # Ensure the root node is a function call
    if not isinstance(tree.body, ast.Call):
        raise ValueError("Input is not a valid function call expression")
    
    # Iterate over the arguments of the function call
    args = []
    for arg in tree.body.args:
        if isinstance(arg, ast.Name):  
            return None
        # Use ast.literal_eval to safely evaluate the argument as a Python object
        try:
            evaluated_arg = ast.literal_eval(arg)
        except (ValueError, SyntaxError):
            evaluated_arg = eval(compile(ast.Expression(arg), "<string>", "eval"))

        args.append(evaluated_arg)
    
    return args
    
def extract_statements(statements):
    result = []
    for statement in statements:
        try:
            test_inputs = extract_test_inputs_from_statement(statement)
            if test_inputs:
                result.append(test_inputs)
        except:
            continue
    return result

def random_sample(lst, k, seed=2345):
    random.seed(seed)
    k = min(k, len(lst))
    indices = random.sample(range(len(lst)), k)  
    samples = [lst[i] for i in indices]  
    return samples, indices
    
def args_2_statement(args, func_name, no_repr_indexs=[]):
    args_str = ", ".join(repr(arg) if i not in no_repr_indexs else arg for i, arg in enumerate(args))
    return f"{func_name}({args_str})"

def get_comb_test_inputs(comb_test, comb_name, function_args):
    test_inputs = []
    for assert_code in comb_test:
        test_cases = extract_test_inputs_from_assert(assert_code)
        test_inputs.extend(test_cases)
    
    test_input_list = []
    for func_name, args in test_inputs:
        if func_name == comb_name and len(args) == len(function_args):
            test_input_list.append(args)
    return test_input_list

def cover_all_lists_randomly(lists, seed=1234):

    if not lists or any(not lst for lst in lists):
        raise ValueError("Input lists must not be empty")
    
    random.seed(seed)
    
    original_lists = [lst[:] for lst in lists]
    max_length = max(len(lst) for lst in lists)
    current_lists = [lst[:] for lst in lists]
    result = []
    
    for _ in range(max_length):
        combination = []
        for i, current_list in enumerate(current_lists):
            if not current_list:
                current_lists[i] = original_lists[i][:]
            chosen = random.choice(current_lists[i])
            current_lists[i].remove(chosen)
            combination.append(chosen)
        
        result.append(tuple(combination))
    
    return result

def cover_all_lists(lists):
     product_list = list(itertools.product(*lists))
     return product_list

def replace_at_index(lst: list, index: int, new_elements: list) -> list:
    if not (0 <= index < len(lst)):
        raise IndexError("Index out of range")
    return lst[:index] + new_elements + lst[index + 1:]

def extract_args_str_from_prompt(prompt: str) -> List[str]:
    tree = ast.parse(prompt)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            arg_names = [arg.arg for arg in node.args.args]
            return arg_names
    return []

def get_str_index(lst, str):
    return [i for i, x in enumerate(lst) if x == str]


def choose_comb_tasks(comb_dict, tgt_type):
    candi_comb_tasks = list()
    for task_id, comb_task in comb_dict.items():
        comb_output_types = comb_task['input_output_types'][1]
        if len(comb_output_types) == 1 and comb_output_types[0] == tgt_type:
            candi_comb_tasks.append(comb_task)
    return candi_comb_tasks

def choose_comb_task(candi_comb_tasks, docstring):
    candidate_texts = [task['text'] for task in candi_comb_tasks]
    similaritys = getSimilarity([docstring], candidate_texts)
    for i in range(len(candi_comb_tasks)):
        candi_comb_tasks[i]['similarity'] = similaritys[i]
    candi_comb_tasks = sorted(candi_comb_tasks, key=lambda x: x['similarity'], reverse=True)
    # top 5
    candi_comb_tasks_top5 = candi_comb_tasks[:5]
    comb_task = candi_comb_tasks_top5[0]
    return comb_task

def unique_types_in_order(input_type_comb):
    """
    Get unique types from input_type_comb in their first appearance order.

    Args:
        input_type_comb (list): A list of input types.

    Returns:
        list: A list of unique types in their first appearance order.
    """
    seen = set()
    input_types = []
    for input_type in input_type_comb:
        if input_type not in seen:
            seen.add(input_type)
            input_types.append(input_type)
    return input_types



def mutant_init(seed_benchmark_path, comb_benchmark_path, output_path):

    # set logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(output_path+"/mutant_init.log")
    file_handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Start to initialize mutants")
    
    seed_benchmark = read_json(seed_benchmark_path)
    seed_benchmark_name = os.path.basename(seed_benchmark_path).split(".")[0]
    comb_benchmark = read_jsonl(comb_benchmark_path)
    comb_benchmark_name = os.path.basename(comb_benchmark_path).split(".")[0]

    mutant_results = list()

    comb_dict = dict()

    if os.path.exists(output_path+"/comb_dict.json"):
        comb_dict = read_json(output_path+"/comb_dict.json")
    else:
        # if comb_benchmark_name == "mbpp-unsanitized":
        for i in tqdm(range(len(comb_benchmark))):
            
            task = json.loads(comb_benchmark[i])
            text = task["text"]
            code = task["code"]
            task_id = task["task_id"]
            # 698: test case use tuple as key of dict, which is not supported
            if task_id in [698]:
                continue
            entry_point, function_name, arg_names = extract_code_before_function_signature(code)
            # if function_name == 'heap_queue_largest':
            #     pass
            #     print(1)
            test_list = task["test_list"] + task["challenge_test_list"]
            test_list = filter_test_list(test_list, function_name, arg_names)
            if len(test_list) == 0:
                continue
            try:
                input_output_types = type_match.get_input_output_types_py(test_list)
            except Exception as e:
                continue
            comb_dict[task_id] = {"text": text, "code": code, "entry_point": entry_point, "function_name": function_name, "test_list": test_list, "input_output_types": input_output_types, "arg_names": arg_names}
        logger.info("Generate comb dict finished")
        write_json(output_path+"/comb_dict.json", comb_dict)
        # elif comb_benchmark_name == "odex_filtered_data":
        #     for i in tqdm(range(len(comb_benchmark))):
        #         task = json.loads(comb_benchmark[i])
        #         text = task["intent"]
        #         code = task["prompt"]+task["canonical_solution"]
        #         task_id = task["odex_task_id"]
        #         entry_point, function_name, arg_names = extract_code_before_function_signature(code)
        #         test_list = task["filtered_test_assertions"]
        #         # test_list = filter_test_list(test_list, function_name, arg_names)
        #         if len(test_list) == 0:
        #             continue
        #         try:
        #             output_types = type_match.get_output_types_py(test_list)
        #         except Exception as e:
        #             continue
        #         comb_dict[task_id] = {"text": text, "code": code, "entry_point": entry_point, "function_name": function_name, "test_list": test_list, "output_types": output_types, "arg_names": arg_names}
        #    write_json(output_path+"/comb_dict.json", comb_dict)

    for task in tqdm(seed_benchmark, desc="Processing tasks"):
        result = copy.deepcopy(task)
        # if seed_benchmark_name == "Humaneval":

        #     entry_point = result['entry_point']
        # elif seed_benchmark_name == "mbpp-sanitized":
        #     _, function_name, _ = extract_code_before_function_signature(code)
        #     entry_point = function_name
        #     result['entry_point'] = entry_point
        # canonical_solution = result['canonical_solution']

        name = result['name']
        pos = name.find("_", name.find("_") + 1)
        result['task_id'] = name[:pos]
        result['entry_point'] = name[pos + 1:]
        entry_point = result['entry_point']



        prompt = result['prompt']
        # canonical_solution_code = prompt + canonical_solution
        
        docstring = extract_docstring(prompt, entry_point)
        arg_names = extract_args_str_from_prompt(prompt)
        
        tests = result['tests']
        try:
            # input_output_types = type_match.get_input_output_types_py(extract_assert_statements(test))
            # prompt_calls = extract_method_calls(docstring, entry_point)
            assert_statements = extract_assert_statements(tests)
            prompt_calls = [extract_prompt_call_from_assert(assert_statement) for assert_statement in assert_statements]
            input_types, input_type_combs, correct_calls, arg_types_to_statement = type_match.get_input_types_by_call(prompt_calls)

        except Exception as e:
            continue
        result["test_asserts"] = assert_statements
        result['input_types'] = input_types
        result['input_type_combs'] = input_type_combs
        result['sample_calls'] = correct_calls
        if len(input_types) == 0:
            continue

        # mutant 1
        if len(input_types) ==1 and len(input_type_combs[0])==1:
            mutant_1 = dict()
            input_type = input_types[0]
            statements = arg_types_to_statement[tuple(input_type_combs[0])]
            mutant_1['statements'] = statements
            statements_inputs = extract_statements(statements)
            mutant_1['statements_inputs'] = statements_inputs
            candi_comb_tasks = choose_comb_tasks(comb_dict, input_type)
            # choose the comb task with the most similar code
            if len(candi_comb_tasks) > 0:
                comb_task = choose_comb_task(candi_comb_tasks, docstring)
                mutant_1['comb_task_top'] = comb_task
                comb_task_prompt, mutant_prompt, mutant_entry_point = prompt_gen.mutant1_prompt(prompt, entry_point, comb_task)
                mutant_1['comb_task_prompt'] = comb_task_prompt
                mutant_1['mutant_prompt'] = mutant_prompt
                mutant_1['mutant_entry_point'] = mutant_entry_point

                comb_test_inputs = get_comb_test_inputs(comb_task['test_list'], comb_task['function_name'], comb_task['arg_names'])
                mutant_1['comb_test_inputs'] = comb_test_inputs
                mt_assert_list = list()
                comb_name = comb_task['function_name']
                for test_input in comb_test_inputs:
                    args_str = ", ".join(repr(arg) for arg in test_input)
                    mt_assert = f"assert {entry_point}({comb_name}({args_str})) == {mutant_entry_point}({args_str})"
                    mt_assert_list.append(mt_assert)
                mt_assert_list = list(set(mt_assert_list))
                mutant_1['mt_assert_list'] = mt_assert_list
                mutant_1['seed_is_single_input'] = True
                result['mutant_1'] = [mutant_1]
            else:
                result['mutant_1'] = []
        else:
            mutant_1 = list()
            for input_type_comb in input_type_combs:
                # only consider the input type combination with the same length as the arg_names
                if len(input_type_comb) != len(arg_names):
                    continue
                key = tuple(input_type_comb)
                statements = arg_types_to_statement[key]
                statements_inputs = extract_statements(statements)
                if len(statements_inputs) == 0:
                    continue
                for input_type_id in range(len(input_type_comb)):
                    mutant_1_item = dict()
                    mutant_1_item['input_type_id'] = input_type_id
                    mutant_1_item['statements'] = statements
                    mutant_1_item["statements_input"] = statements_inputs
                    input_type = input_type_comb[input_type_id]
                    candi_comb_tasks = choose_comb_tasks(comb_dict, input_type)
                    # choose the comb task with the most similar code
                    if len(candi_comb_tasks) > 0:
                        comb_task = choose_comb_task(candi_comb_tasks, docstring)
                        # mutant_1_item['comb_tasks_top5'] = candi_comb_tasks_top5
                        mutant_1_item['comb_task_top'] = comb_task
                        comb_task_prompt, mutant_prompt, mutant_entry_point = prompt_gen.mutant1_multi_prompt(prompt, entry_point, comb_task, input_type_id, arg_names)
                        mutant_1_item['comb_task_prompt'] = comb_task_prompt
                        mutant_1_item['mutant_prompt'] = mutant_prompt
                        mutant_1_item['mutant_entry_point'] = mutant_entry_point
                        comb_test_inputs = get_comb_test_inputs(comb_task['test_list'], comb_task['function_name'], comb_task['arg_names'])
                        mutant_1_item["comb_test_inputs"] = comb_test_inputs
                        mt_assert_list = list()
                        comb_name = comb_task['function_name']
                        
                        # get combinations of test inputs and seed statements
                        all_lists = list()
                        all_lists.append(statements_inputs)
                        all_lists.append(comb_test_inputs)
                        mutant_1_item["all_lists"] = all_lists
                        test_input_combinations = cover_all_lists(all_lists)
                        for test_input_comb in test_input_combinations:
                            left_args = copy.deepcopy(test_input_comb[0])
                            comb_statement = args_2_statement(test_input_comb[1], comb_name)
                            left_args[input_type_id] = comb_statement
                            left_statement = args_2_statement(left_args, entry_point, [input_type_id])
                            right_args = copy.deepcopy(test_input_comb[0])
                            right_args = replace_at_index(right_args, input_type_id, test_input_comb[1])
                            right_statement = args_2_statement(right_args, mutant_entry_point)
                            mt_assert = f"assert {left_statement} == {right_statement}"
                            mt_assert_list.append(mt_assert)
                        mt_assert_list = list(set(mt_assert_list))
                        mutant_1_item['mt_assert_list'] = mt_assert_list
                        mutant_1_item["seed_is_single_input"] = False
                        mutant_1.append(mutant_1_item)
            
            result['mutant_1'] = mutant_1

        # mutant 2: change all inputs of a type to the output of another function
        mutant_2 = list()
        candi_comb_tasks = list()
        for input_type_comb in input_type_combs:
            if len(input_type_comb) != len(arg_names):
                continue
            key = tuple(input_type_comb)
            statements = arg_types_to_statement[key]
            statements_inputs = extract_statements(statements)
            if len(statements_inputs) == 0:
                continue
            input_types = list(set(input_type_comb))
            for input_type in input_types:
                mutant_2_item = dict()
                input_type_indexs = get_str_index(input_type_comb, input_type)
                mutant_2_item["input_type_indexs"] = input_type_indexs
                mutant_2_item['statements'] = statements
                mutant_2_item['statements_inputs'] = statements_inputs
                if len(input_type_indexs) == 1:
                    continue
                candi_comb_tasks = choose_comb_tasks(comb_dict, input_type)
                if len(candi_comb_tasks) > 0:
                    comb_task = choose_comb_task(candi_comb_tasks, docstring)
                    mutant_2_item['comb_task_top'] = comb_task
                    comb_task_prompt, mutant_prompt, mutant_entry_point = prompt_gen.mutant2_prompt(prompt, entry_point, comb_task, input_type_indexs, arg_names)
                    mutant_2_item['comb_task_prompt'] = comb_task_prompt
                    mutant_2_item['mutant_prompt'] = mutant_prompt
                    mutant_2_item['mutant_entry_point'] = mutant_entry_point
                    comb_test_inputs = get_comb_test_inputs(comb_task['test_list'], comb_task['function_name'], comb_task['arg_names'])
                    mutant_2_item["comb_test_inputs"] = comb_test_inputs
                    mt_assert_list = list()
                    comb_name = comb_task['function_name']

                    # get combinations of test inputs and seed statements
                    all_lists = list()
                    all_lists.append(statements_inputs)
                    for input_type_index in input_type_indexs:
                        all_lists.append(comb_test_inputs)
                    mutant_2_item["all_lists"] = all_lists
                    test_input_combinations = cover_all_lists(all_lists)
                    for test_input_comb in test_input_combinations:
                        left_args = copy.deepcopy(test_input_comb[0])
                        for i in range(len(input_type_indexs)):
                            left_args[input_type_indexs[i]] = args_2_statement(test_input_comb[i+1], comb_name)
                        left_statement = args_2_statement(left_args, entry_point, input_type_indexs)
                        right_args = copy.deepcopy(test_input_comb[0])
                        for i in range(len(input_type_indexs) - 1, -1, -1):  
                            right_args = replace_at_index(right_args, input_type_indexs[i], test_input_comb[i + 1])
                        right_statement = args_2_statement(right_args, mutant_entry_point)
                        mt_assert = f"assert {left_statement} == {right_statement}"
                        mt_assert_list.append(mt_assert)
                    mt_assert_list = list(set(mt_assert_list))
                    mutant_2_item['mt_assert_list'] = mt_assert_list
                    mutant_2.append(mutant_2_item)
        result['mutant_2'] = mutant_2
                    
        # mutant3: change all inputs of all types to the output of another function
        mutant_3 = list()
        candi_comb_tasks = list()
        for input_type_comb in input_type_combs:
            if len(input_type_comb) != len(arg_names):
                continue
            key = tuple(input_type_comb)
            statements = arg_types_to_statement[key]
            statements_inputs = extract_statements(statements)
            
            if len(statements_inputs) == 0:
                continue
            input_types = unique_types_in_order(input_type_comb)
            input_type_to_comb_task = dict()
            index_to_input_types = dict()
            input_types_mutanted = list()
            for input_type in input_types:
                input_type_indexs = get_str_index(input_type_comb, input_type)
                
                comb_tasks = choose_comb_tasks(comb_dict, input_type)
                if len(comb_tasks) > 0:
                    comb_task = choose_comb_task(comb_tasks, docstring)
                    input_type_to_comb_task[input_type] = comb_task
                    for index in input_type_indexs:
                        index_to_input_types[index] = input_type
                    input_types_mutanted.append(input_type)
            if len(input_type_to_comb_task.keys()) < 2:
                continue    
            mutant_3_item = dict()
            mutant_3_item['statements'] = statements
            mutant_3_item['statements_inputs'] = statements_inputs
            mutant_3_item['input_type_to_comb_task'] = input_type_to_comb_task
            mutant_3_item['index_to_input_types'] = index_to_input_types
            comb_task_prompts, comb_task_names, mutant_prompt, mutant_entry_point = prompt_gen.mutant3_prompt(prompt, entry_point, input_type_to_comb_task, index_to_input_types, input_types_mutanted, arg_names)
            mutant_3_item['comb_task_prompts'] = comb_task_prompts
            mutant_3_item['comb_task_names'] = comb_task_names
            mutant_3_item['mutant_prompt'] = mutant_prompt
            mutant_3_item['mutant_entry_point'] = mutant_entry_point

            comb_type_to_test_inputs = dict()
            comb_type_to_func_name = dict()
            for input_type in input_type_to_comb_task.keys():
                comb_test_inputs = get_comb_test_inputs(input_type_to_comb_task[input_type]['test_list'], input_type_to_comb_task[input_type]['function_name'], input_type_to_comb_task[input_type]['arg_names'])
                comb_type_to_test_inputs[input_type] = comb_test_inputs
                comb_type_to_func_name[input_type] = input_type_to_comb_task[input_type]['function_name']
            mt_assert_list = list()
            mutant_3_item["comb_type_to_test_inputs"] = comb_type_to_test_inputs
            mutant_3_item["comb_type_to_func_name"] = comb_type_to_func_name
            # get combinations of test inputs and seed statements
            all_lists = list()
            all_lists.append(statements_inputs)
            sorted_input_indexs = sorted(index_to_input_types.keys())
            mutant_3_item["sorted_input_indexs"] = sorted_input_indexs
            for index in sorted_input_indexs:
                all_lists.append(comb_type_to_test_inputs[index_to_input_types[index]])
            mutant_3_item["all_lists"] = all_lists
            test_input_combinations = cover_all_lists(all_lists)
            for test_input_comb in test_input_combinations:
                left_args = copy.deepcopy(test_input_comb[0])
                for i in range(len(sorted_input_indexs)):
                    left_args[sorted_input_indexs[i]] = args_2_statement(test_input_comb[i+1], comb_type_to_func_name[index_to_input_types[sorted_input_indexs[i]]])
                left_statement = args_2_statement(left_args, entry_point, sorted_input_indexs)
                right_args = copy.deepcopy(test_input_comb[0])
                for i in range(len(sorted_input_indexs) - 1, -1, -1):  
                    right_args = replace_at_index(right_args, sorted_input_indexs[i], test_input_comb[i + 1])
                right_statement = args_2_statement(right_args, mutant_entry_point)
                mt_assert = f"assert {left_statement} == {right_statement}"
                mt_assert_list.append(mt_assert)
            mt_assert_list = list(set(mt_assert_list))
            mutant_3_item['mt_assert_list'] = mt_assert_list
            mutant_3.append(mutant_3_item)
        result['mutant_3'] = mutant_3

        if len(result['mutant_1'])>0:
            sample_mutant_1, sample_id = random_sample(result["mutant_1"], 1)
            result["mutant_1_item_sample_id"] = sample_id
            mutant_1_sampled_item = sample_mutant_1[0]
            result["mutant_1_item"] = mutant_1_sampled_item
        if len(result['mutant_2'])>0:
            sample_mutant_2, sample_id = random_sample(result["mutant_2"], 1)
            result["mutant_2_item_sample_id"] = sample_id
            mutant_2_sampled_item = sample_mutant_2[0]
            result["mutant_2_item"] = mutant_2_sampled_item
        if len(result['mutant_3'])>0:
            sample_mutant_3, sample_id = random_sample(result["mutant_3"], 1)
            result["mutant_3_item_sample_id"] = sample_id
            mutant_3_sampled_item = sample_mutant_3[0]
            result["mutant_3_item"] = mutant_3_sampled_item
                    
        # we first only consider tasks with mutant
        if len(result['mutant_1']) > 0 or len(result['mutant_2']) > 0 or len(result['mutant_3']) > 0:
            mutant_results.append(result)
            write_jsonl(output_path+"/mutant_results_init.jsonl", mutant_results)
        # else:
        #     print(1)
    
    logger.info("Finish initializing mutants")

        





if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed_benchmark_path', type=str)
    parser.add_argument('--comb_benchmark_path', type=str)
    parser.add_argument('--output_path', type=str)

    args = parser.parse_args()

    seed_benchmark_path = args.seed_benchmark_path
    comb_benchmark_path = args.comb_benchmark_path
    output_path = args.output_path

    # data_folder = "../../datasets/benchmarks/"
    # seed_benchmark_name = "human-eval"
    # seed_benchmark_path = data_folder + "humaneval-py-transform.json"
    # # seed_benchmark_path = data_folder + "mbpp/mbpp-sanitized.jsonl"
    # comb_benchmark_path = data_folder + "mbpp-py-reworded.json"
    # output_path = f"../../mutant/results/init_{seed_benchmark_name}_vner4test"
    # if not os.path.exists(output_path):
    #     os.makedirs(output_path
    # )


    mutant_init(seed_benchmark_path, comb_benchmark_path, output_path)