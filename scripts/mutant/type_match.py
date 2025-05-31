import ctree
import ast
import astor
import re
import spacy
import ipaddress

def parse_assertion(assert_statement):
    # Parse the function call into an AST
    tree = ast.parse(assert_statement)

    # Find the function call node
    call_node = next(
        node for node in ast.walk(tree) if isinstance(node, ast.Call)
    )

    # Extract the arguments
    args = []
    for arg in call_node.args:
        args.append(eval(astor.to_source(arg)))

    output_node = tree.body[0].test.comparators[0]
    if isinstance(output_node, ast.List):
        output_vars = [eval(astor.to_source(d)) for d in output_node.elts]
    else:
        output_vars = eval(astor.to_source(output_node))
    # print(args, output_vars)
    return args, output_vars

def parse_call(call_statement):
    # Parse the function call into an AST
    tree = ast.parse(call_statement)

    # Find the function call node
    call_node = next(
        node for node in ast.walk(tree) if isinstance(node, ast.Call)
    )

    # Extract the arguments
    args = []
    for arg in call_node.args:
        args.append(eval(astor.to_source(arg)))
    return args


def get_list_element_type(list_a):
    possible_types = summarize_types(list_a)
    possible_type_str = ','.join(possible_types)
    return f"list[{possible_type_str}]"


def get_tuple_element_type(tuple_a):
    possible_types = summarize_types(tuple_a)
    possible_type_str = ','.join(possible_types)
    return f"tuple[{possible_type_str}]"


def get_dict_element_type(dict_a):
    map_list = set()
    for k in dict_a:
        v = dict_a[k]
        map_list.add(type(v).__name__)
    possible_type_str = ','.join(list(map_list))
    return f"dict[{possible_type_str}]"

def find_url(string):
	# findall() has been used
	# with valid conditions for urls in string
    #  from https://proxiesapi.com/articles/extracting-urls-from-text-in-python
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    urls = [x[0] for x in url]
    domain_regex = r"\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
    domains = re.findall(domain_regex, string)
    results = urls + domains
    return results

def extract_paths(text):
    # from https://regex101.com/r/IsmBeL
    pattern = r"(?:[A-Z]:|\\|(?:\.{1,2}[\/\\])+)[\w+\\\s_\(\)\/]+(?:\.\w+)*"
    pattern2 = r"/(?:[\w\s_\(\)-]+/)*[\w\s_\(\)-]*"

    paths = re.findall(pattern, text)
    paths.extend(re.findall(pattern2,text))
    # pattern_windows = r'(\\[a-zA-Z\.\\]*[\s]?)'
    # paths_windows = re.findall(pattern_windows, text)
    # paths.extend(paths_windows)
    return paths

def contains_ip_address(text):
    """
    Check if a given string contains a valid IP address or CIDR notation.
    
    Args:
        text (str): Input string.
    
    Returns:
        bool: True if a valid IP address or CIDR is found, otherwise False.
    """
    # Regular expression to extract potential IPv4 addresses or CIDR notation
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b'
    
    # Find all potential IP addresses in the text
    candidates = re.findall(ip_pattern, text)
    
    # Validate each candidate using ipaddress library
    for candidate in candidates:
        try:
            ipaddress.ip_network(candidate, strict=False)  # Allow single IPs and CIDR notation
            return True  # Return True if a valid IP or CIDR is found
        except ValueError:
            continue  # Ignore invalid IP addresses and continue checking
    
    return False  # No valid IP address found

def is_filename(string: str) -> bool:
    pattern = r"^[\w,\s-]+\.[A-Za-z0-9]{2,5}$"
    
    return bool(re.match(pattern, string))

def get_str_ner(text):
    nglish_model = spacy.load("en_core_web_sm")
    processed_text = nglish_model(text)
    entities = [ent.label_ for ent in processed_text.ents]
    # detect url in the string
    urls = find_url(text)
    if urls:
        entities.append('URL')

    if contains_ip_address(text):
         entities.append('IP ADDRESS')

    # detect paths in the string
    paths = extract_paths(text)
    if paths:
        entities.append('PATH')

    if is_filename(text):
        entities.append('FILENAME')
    return entities


def summarize_types(val_list):
    possible_types = set()
    for v in val_list:
        if v is None:
            continue
        type_name = type(v).__name__
        if type_name in ['bool', 'int',  'float']:
            possible_types.add(type_name)
        elif type_name == 'str':
            string_ner = get_str_ner(v)
            possible_types.add('str'+f" entitys: [{string_ner}]")
        elif type_name == 'list':
            new_type_name = get_list_element_type(v)
            possible_types.add(new_type_name)
        elif type_name == 'tuple':
            new_type_name = get_tuple_element_type(v)
            possible_types.add(new_type_name)
        elif type_name == 'dict':
            new_type_name = get_dict_element_type(v)
            possible_types.add(new_type_name)
        else:
            raise NotImplementedError
    return list(possible_types)

def summarize_types_byorder(val_list):
    possible_types = list()
    for v in val_list:
        if v is None:
            continue
        type_name = type(v).__name__
        if type_name in ['bool', 'int', 'float']:
            possible_types.append(type_name)
        elif type_name == 'str':
            string_ner = get_str_ner(v)
            possible_types.append('str'+f" entitys: [{string_ner}]")
        elif type_name == 'list':
            new_type_name = get_list_element_type(v)
            possible_types.append(new_type_name)
        elif type_name == 'tuple':
            new_type_name = get_tuple_element_type(v)
            possible_types.append(new_type_name)
        elif type_name == 'dict':
            new_type_name = get_dict_element_type(v)
            possible_types.append(new_type_name)
        else:
            raise NotImplementedError
    return possible_types


def get_input_output_types_py(assert_statements):
    args_list, output_var_list = [], []
    for statement in assert_statements:
        arguments, expected_output = parse_assertion(statement)

        args_list.append(arguments)
        output_var_list.append(expected_output)

    args_list = list(zip(*args_list))
    all_input_types = []
    for args in args_list:
        input_types = summarize_types(args)
        all_input_types.append(input_types)
    output_types = summarize_types(output_var_list)
    return all_input_types, output_types

def get_output_types_py(assert_statements):
    output_var_list = []
    for statement in assert_statements:
        arguments, expected_output = parse_assertion(statement)
        output_var_list.append(expected_output)

    output_types = summarize_types(output_var_list)
    return output_types

def f(a):
    for x in range(10):
        a[x] += x

def get_input_types_by_call(call_statements):
    args_list = []
    arg_types_list = []
    correct_statements = []
    arg_types_to_statement = {}
    for statement in call_statements:
        try:
            arguments = parse_call(statement)
            arg_types = summarize_types_byorder(arguments)
            if arg_types not in arg_types_list:
                arg_types_list.append(arg_types)
                arg_types_to_statement[tuple(arg_types)] = [statement]
            else:
                arg_types_to_statement[tuple(arg_types)].append(statement)
            args_list.extend(arg_types)
            correct_statements.append(statement)
            
        except Exception as e:
            continue
    

    all_input_types = list(set(args_list))
    # for args in args_list:
    #     input_types = summarize_types(args)
    #     all_input_types.append(input_types)
    
    return all_input_types, arg_types_list, correct_statements, arg_types_to_statement



# print(get_input_output_types_py(["assert f([1, 2, 3]) == [1, 3, 5]", "assert f([1, 2, 3]) == [1, 3, 5]"]))

# print(summarize_types_byorder([["a", 2.8, 3.0, 4.0, 5.0, 2.0], 0.3]))

# print(get_input_types_by_call(["separate_paren_groups('www.baidu.com')", "separate_paren_groups('1', [1,2])"]))
