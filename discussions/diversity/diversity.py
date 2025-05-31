import nltk
import numpy as np
from tqdm import tqdm
from nltk.translate.bleu_score import sentence_bleu
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch
import json

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")



def read_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def write_json(file_path: str, data):
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f]
    
    

def write_jsonl(file_path, lst):
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in lst:
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + '\n')

def compute_bleu(base_sentences, new_sentences):

    new_sentences = [nltk.word_tokenize(text.lower()) for text in new_sentences]
    base_sentences = [nltk.word_tokenize(text.lower()) for text in base_sentences]

    if len(new_sentences) != len(base_sentences):
        return np.nan

    n = len(new_sentences)
    total_bleu_score = 0.0

    for i in tqdm(range(n)):
        ref_sentences = [base_sentences[i]]
        hypothesis = new_sentences[i]
        bleu_score = sentence_bleu(ref_sentences, hypothesis)
        total_bleu_score += bleu_score

    self_bleu_score = total_bleu_score / (n + 1e-12)
    return self_bleu_score

def compute_embeding_sim(base_sentences, new_sentences, model):
    
    vec1 = model.encode(base_sentences)
    vec2 = model.encode(new_sentences)
    if len(vec2) == 0:
        return 0.0
    cos_sim = cosine_similarity(vec1, vec2)
    sim = np.diagonal(cos_sim)
    return float(np.mean(sim))

def baseline_list_to_dict(lst):
    result = {}
    for item in lst:
        result[item["task_id"]] = item["prompt"]
    return result

if __name__ == "__main__":
    # baselines diversity
    model = SentenceTransformer('../../../code_models/sentence-transformers/bert-base-nli-mean-tokens')
    model = model.to(device).eval()
    result_dict = {}
    baselines = ["base", "comment", "insert_line", "output_mutation", "output_v_mutation"]
    dataset_to_filename = {"humaneval": "init_human-eval_vner4", "mbpp": "init_mbpp-sanitized_vner4"}
    for dataset in ["humaneval", "mbpp"]:
        result_dict[dataset] = {}
        base_file = read_jsonl(f"../../baselines/datasets/{dataset}/base/{dataset}_base.jsonl")
        base_id_to_prompt = baseline_list_to_dict(base_file)
        for baseline in baselines:
            baseline_file = read_jsonl(f"../../baselines/datasets/{dataset}/{baseline}/{dataset}_{baseline}.jsonl")
            baseline_id_to_prompt = baseline_list_to_dict(baseline_file)
            base_sentences = []
            baseline_sentences = []
            for task_id in base_id_to_prompt:
                if task_id not in baseline_id_to_prompt:
                    continue
                base_sentences.append(base_id_to_prompt[task_id])
                baseline_sentences.append(baseline_id_to_prompt[task_id])
            bleu = compute_bleu(base_sentences, baseline_sentences)
            embedding_sim = compute_embeding_sim(base_sentences, baseline_sentences, model)
            result_dict[dataset][baseline] = {"bleu": bleu, "embedding_sim": embedding_sim}
            
        # combmt diversity
        mutant_path = f"../../mutant/results/{dataset_to_filename[dataset]}/mutant_results_init.jsonl"
        mutant_1_base_prompts = []
        mutant_1_mutant_prompts = []
        mutant_2_base_prompts = []
        mutant_2_mutant_prompts = []
        mutant_3_base_prompts = []
        mutant_3_mutant_prompts = []
        mutant_tasks = read_jsonl(mutant_path)
        for task in mutant_tasks:
            if "mutant_1_item" in task:
                mutant_1_item = task["mutant_1_item"]
                mutant_1_base_prompts.append(task["prompt"])
                mutant_1_mutant_prompts.append(mutant_1_item["mutant_prompt"])
            if "mutant_2_item" in task:
                mutant_2_item = task["mutant_2_item"]
                mutant_2_base_prompts.append(task["prompt"])
                mutant_2_mutant_prompts.append(mutant_2_item["mutant_prompt"])
            if "mutant_3_item" in task:
                mutant_3_item = task["mutant_3_item"]
                mutant_3_base_prompts.append(task["prompt"])
                mutant_3_mutant_prompts.append(mutant_3_item["mutant_prompt"])
        bleu = compute_bleu(mutant_1_base_prompts, mutant_1_mutant_prompts)
        embedding_sim = compute_embeding_sim(mutant_1_base_prompts, mutant_1_mutant_prompts, model)
        result_dict[dataset]["mutant_1"] = {"bleu": bleu, "embedding_sim": embedding_sim}
        bleu = compute_bleu(mutant_2_base_prompts, mutant_2_mutant_prompts)
        embedding_sim = compute_embeding_sim(mutant_2_base_prompts, mutant_2_mutant_prompts, model)
        result_dict[dataset]["mutant_2"] = {"bleu": bleu, "embedding_sim": embedding_sim}
        bleu = compute_bleu(mutant_3_base_prompts, mutant_3_mutant_prompts)
        embedding_sim = compute_embeding_sim(mutant_3_base_prompts, mutant_3_mutant_prompts, model)
        result_dict[dataset]["mutant_3"] = {"bleu": bleu, "embedding_sim": embedding_sim}
    write_json("diversity.json", result_dict)
            

