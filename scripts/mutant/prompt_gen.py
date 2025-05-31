import ast
from typing import List

def extract_function_with_prior_content(code: str):
    tree = ast.parse(code)
    
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            func_start_line = node.lineno
            
            lines = code.splitlines()
            header_and_prior_content = "\n".join(lines[:func_start_line])
            
            docstring = ast.get_docstring(node)
            
            return header_and_prior_content, docstring
    
    return None, None  

def generate_unique_var_name(base_name, index):
    return f"{base_name}_{index}"

def number_2_text(num):
    num += 1
    if 10 <= num % 100 <= 13:
        suffix = "th"
    else:
        last_digit = num % 10
        if last_digit == 1:
            suffix = "st"
        elif last_digit == 2:
            suffix = "nd"
        elif last_digit == 3:
            suffix = "rd"
        else:
            suffix = "th"
    return f"{num}{suffix}"

def intend_prompt(prompt):
    return "\n".join("        " + line if line else line for line in prompt.split("\n"))

def change_def_name_args(code: str, change_indexes: List, change_args_list: List[List[str]], mutant_entry_point: str) -> str:
    tree = ast.parse(code)
    result_lines = []
    
    for node in tree.body:
        # Check whether it is a function definition node
        if isinstance(node, ast.FunctionDef):
            for index, new_args in sorted(zip(change_indexes, change_args_list), reverse=True):
                if index < 0 or index >= len(node.args.args):
                    raise ValueError(f"Index {index} out of range for function arguments")
                
                # Replace the argument at the specified index with the new arguments
                original_args = node.args.args
                node.args.args = (
                    original_args[:index] +
                    [ast.arg(arg=arg, annotation=None) for arg in new_args] +
                    original_args[index + 1:]
                ) 
            arg_names = [arg.arg for arg in node.args.args]
            function_signature = f"def {mutant_entry_point}({', '.join(arg_names)}):"
            result_lines.append(function_signature)
            break
        else:
            # Non-function definition node, add code directly
            result_lines.append(ast.get_source_segment(code, node))

    return '\n'.join(result_lines)

def generate_unique_var_name(base_name, index):
    return f"{base_name}_{index}"

def format_re_ids(re_ids):
    if not re_ids:
        return ""
    if len(re_ids) == 1:
        return re_ids[0]
    if len(re_ids) == 2:
        return f"{re_ids[0]} and {re_ids[1]}"
    # For more than 2 items, join with commas and add 'and' before the last item
    return ", ".join(re_ids[:-1]) + ", and " + re_ids[-1]

def generate_mutant_name_abbreviation(seed_func_name, input_funcs):
    abbreviations = input_funcs
    return f"{seed_func_name}_" + "_".join(abbreviations)

def format_comb_task_with_mapping(comb_task_mapping):
    formatted = []
    for func_desc, inputs in comb_task_mapping.items():
        input_list = format_re_ids([f"{input_var} ({number_2_text(i)} input)" for i, input_var in inputs])
        formatted.append(f"{func_desc}\n    (Replaces inputs: {input_list})")
    return "\n\n".join(formatted)

def format_re_ids_with_params(re_ids, parameter_names):
    descriptions = [
        f"{re_id} parameter ({param_name})"
        for re_id, param_name in zip(re_ids, parameter_names)
    ]
    if len(descriptions) > 1:
        return ", ".join(descriptions[:-1]) + f", and {descriptions[-1]}"
    else:
        return descriptions[0]

def mutant1_prompt(seed_code_prompt, seed_entry_point, comb_task):
    
    comb_text = comb_task["text"]
    comb_task_entry_point = comb_task["entry_point"]
    comb_task_func_name = comb_task["function_name"]
    comb_task_prompt = f"{comb_task_entry_point}\n    \"\"\"{comb_text}\"\"\""
    seed_code_prompt = seed_code_prompt.replace('\"\"\"', "'''")
    comb_task_prompt = comb_task_prompt.replace('\"\"\"', "'''")
    
    mutant_entry_point = comb_task_func_name + "_then_" + seed_entry_point
    mutant_header = comb_task_entry_point.replace(comb_task_func_name, mutant_entry_point)
    # mutant_text = f"Create a function that takes the output of the function \"{comb_text}\" as input for the function \"{seed_docstring}\"."
    comb_task_prompt_indented = intend_prompt(comb_task_prompt)
    seed_code_prompt_indented = intend_prompt(seed_code_prompt)
    mutant_text = (
        f"Create a function that takes the output of the function:\n\n"
        f"{comb_task_prompt_indented}\n\n"
        f"    as input for the function:\n\n"
        f"{seed_code_prompt_indented}"
    )
    mutant_prompt = f"{mutant_header}\n    \"\"\"{mutant_text}    \"\"\""

    return comb_task_prompt, mutant_prompt, mutant_entry_point

def mutant1_multi_prompt(seed_code_prompt, seed_entry_point, comb_task, i, arg_names):
    
    seed_arg_name = arg_names[i]
    comb_text = comb_task["text"]
    comb_task_entry_point = comb_task["entry_point"]
    comb_task_func_name = comb_task["function_name"]
    comb_arg_names = comb_task["arg_names"]
    comb_task_prompt = f"{comb_task_entry_point}\n    \"\"\"{comb_text}\"\"\""
    
    seed_code_prompt = seed_code_prompt.replace('\"\"\"', "'''")
    comb_task_prompt = comb_task_prompt.replace('\"\"\"', "'''")
    re_id = number_2_text(i)
    
    
    mutant_entry_point = comb_task_func_name + "_then_" + seed_entry_point

    comb_arg_names_unique = [generate_unique_var_name(arg, 0) for arg in comb_arg_names]
    mutant_header = change_def_name_args(seed_code_prompt, [i], [comb_arg_names_unique], mutant_entry_point)
    # indent each line of prompts
    comb_task_prompt_indented = intend_prompt(comb_task_prompt)
    seed_code_prompt_indented = intend_prompt(seed_code_prompt)

    mutant_text = (
        f"Create a function that takes the output of the function:\n\n"
        f"{comb_task_prompt_indented}\n\n"
        f"    as input for the {re_id} parameter ({seed_arg_name}) of the function:\n\n"
        f"{seed_code_prompt_indented}"
    )
    mutant_prompt = f"{mutant_header}\n    \"\"\"{mutant_text}    \"\"\""

    return comb_task_prompt, mutant_prompt, mutant_entry_point

def mutant2_prompt(seed_code_prompt, seed_entry_point, comb_task, input_indexs, arg_names):
    comb_text = comb_task["text"]
    comb_task_entry_point = comb_task["entry_point"]
    comb_task_func_name = comb_task["function_name"]
    comb_arg_names = comb_task["arg_names"]
    comb_task_prompt = f"{comb_task_entry_point}\n    \"\"\"{comb_text}\"\"\""
    
    seed_code_prompt = seed_code_prompt.replace('\"\"\"', "'''")
    re_ids = [number_2_text(i) for i in input_indexs]
    arg_names = [arg_names[i] for i in input_indexs]
    formatted_re_ids = format_re_ids_with_params(re_ids, arg_names)
    
    mutant_entry_point = comb_task_func_name + "_then_" + seed_entry_point
    comb_arg_names_unique = [[generate_unique_var_name(arg, i) for arg in comb_arg_names] for i in range(len(input_indexs))]
    mutant_header = change_def_name_args(seed_code_prompt, input_indexs, comb_arg_names_unique, mutant_entry_point)
    # indent each line of prompts
    comb_task_prompt_indented = intend_prompt(comb_task_prompt.replace('\"\"\"', "'''"))
    seed_code_prompt_indented = intend_prompt(seed_code_prompt)
    mutant_text = (
        f"Create a function that takes the output of the function:\n\n"
        f"{comb_task_prompt_indented}\n\n"
        f"    as input for the {formatted_re_ids} parameters of the function:\n\n"
        f"{seed_code_prompt_indented}"
    )
    mutant_prompt = f"{mutant_header}\n    \"\"\"{mutant_text}    \"\"\""
    return comb_task_prompt, mutant_prompt, mutant_entry_point



def mutant3_prompt(prompt, entry_point, input_type_to_comb_task, index_to_input_type, input_types_mutanted, seed_arg_names):
    comb_task_type_to_prompt = dict()
    comb_task_prompts = list()
    comb_task_names = list()
    comb_arg_names_unique = list()
    for input_type in input_types_mutanted:
        comb_task = input_type_to_comb_task[input_type]
        comb_text = comb_task["text"]
        comb_task_entry_point = comb_task["entry_point"]
        
        comb_task_prompt = f"{comb_task_entry_point}\n    \"\"\"{comb_text}\"\"\""

        comb_task_type_to_prompt[input_type] = comb_task_prompt
        comb_task["comb_task_prompt"] = comb_task_prompt
    
    sorted_input_indexs = sorted(index_to_input_type.keys())
    count = 0
    comb_task_prompt_to_seed_args = dict()
    for index in sorted_input_indexs:
        input_type = index_to_input_type[index]
        comb_arg_names = input_type_to_comb_task[input_type]["arg_names"]
        comb_arg_names_unique.append([generate_unique_var_name(arg, count) for arg in comb_arg_names])
        count += 1
        
        comb_task_prompt = comb_task_type_to_prompt[input_type]
        comb_task_name = input_type_to_comb_task[input_type]["function_name"]
        if comb_task_prompt not in comb_task_prompts:
            comb_task_prompts.append(comb_task_prompt)
            comb_task_names.append(comb_task_name)
        comb_task_prompt = comb_task_prompt.replace('\"\"\"', "'''")
        if comb_task_prompt not in comb_task_prompt_to_seed_args:
            comb_task_prompt_to_seed_args[comb_task_prompt] = list()
            
        comb_task_prompt_to_seed_args[comb_task_prompt].append([index, seed_arg_names[index]])

    mutant_entry_point = generate_mutant_name_abbreviation(entry_point, [input_type_to_comb_task[input_type]["function_name"] for input_type in input_types_mutanted])
     
    mutant_header = change_def_name_args(prompt, sorted_input_indexs, comb_arg_names_unique, mutant_entry_point)
    seed_prompt_indented = intend_prompt(prompt.replace('\"\"\"', "'''"))

    mutant_text = (
    f"Create a function that takes the outputs of the following functions:\n\n"
    f"{intend_prompt(format_comb_task_with_mapping(comb_task_prompt_to_seed_args))}\n\n"
    f"    and uses them to replace the inputs of the function:\n\n"
    f"{seed_prompt_indented}"
    )
    mutant_prompt = f"{mutant_header}\n    \"\"\"{mutant_text}    \"\"\""
    return comb_task_prompts, comb_task_names, mutant_prompt, mutant_entry_point



        
       

        
