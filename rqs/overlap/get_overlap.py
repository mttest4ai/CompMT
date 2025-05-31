import json

def read_json(file_path):
    with open(file_path
              , 'r', encoding='utf-8') as f:
        return json.load(f)
    
def write_json(file_path
               , data):
    with open(file_path
              , 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_overlap(lst1, lst2):
    return list(set(lst1) & set(lst2))

def main():
    datasets = ["mbpp-sanitized"]
    models = ["passat10_codegen-2B", "passat10_codegen2-1B", "passat10_incoder-1B", "passat10_santacoder"]
    mutant_types = ["base", "comment", "insert_line", "output_mutation", "output_v_mutation"]
    for dataset in datasets:
        comb_mt_statis = read_json(f"./combmt/{dataset}_static_result.json")
        baselines_statis = read_json(f"./baselines/{dataset}_static_result.json")
        result_dict = {}
        for model in models:
            model_result_dict = {}
            comb_mt_passed = comb_mt_statis[model]["passed"]
            comb_mt_all_passeds = comb_mt_passed["mutant_1_item"] + comb_mt_passed["mutant_2_item"] + comb_mt_passed["mutant_3_item"]
            comb_mt_all_passeds = list(set(comb_mt_all_passeds))
            comb_mt_result = {"mutant_1_item": len(comb_mt_passed["mutant_1_item"]), "mutant_2_item": len(comb_mt_passed["mutant_2_item"]), "mutant_3_item": len(comb_mt_passed["mutant_3_item"]), "all": len(comb_mt_all_passeds)}
            model_result_dict["comb_mt_static"] = comb_mt_result
            all_baseline_passed = []
            for mutant_type in mutant_types:
                baseline_passeds = baselines_statis[model][mutant_type]["passed"]

                all_baseline_passed += baseline_passeds
                overlap = get_overlap(comb_mt_all_passeds, baseline_passeds)
                model_result_dict[mutant_type] = {"over_lap_len": len(overlap), "overlap": overlap, "len_comb_mt": len(comb_mt_all_passeds), "len_baseline": len(baseline_passeds)}
            all_baseline_passed = list(set(all_baseline_passed))
            overlap = get_overlap(comb_mt_all_passeds, all_baseline_passed)
            model_result_dict["all"] = {"over_lap_len": len(overlap), "overlap": overlap, "len_comb_mt": len(comb_mt_all_passeds), "len_baseline": len(all_baseline_passed)}
            result_dict[model] = model_result_dict
        write_json(f"./results/{dataset}_overlap.json", result_dict)


if __name__ == '__main__':
    main()