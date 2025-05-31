import json

def read_jsonl(file_path):
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def write_jsonl(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        for d in data:
            f.write(json.dumps(d, ensure_ascii=False))
            f.write("\n")

def read_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def main():
    sanitized_data = read_json("sanitized-mbpp.json")
    for d in sanitized_data:
        d["text"] = d["prompt"]
        del d["prompt"]
        del d["source_file"]
    full_mbpp_data = read_jsonl("mbpp.jsonl")
    sanitized_ids = set([d["task_id"] for d in sanitized_data])
    unsanitized_data = [d for d in full_mbpp_data if d["task_id"] not in sanitized_ids]
    write_jsonl(unsanitized_data, "mbpp-unsanitized.jsonl")
    write_jsonl(sanitized_data, "mbpp-sanitized.jsonl")




# main
if __name__ == "__main__":
    main()