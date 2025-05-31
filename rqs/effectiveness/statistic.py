import numpy as np
import json
import csv

from scipy.stats import wilcoxon
from statsmodels.stats.multitest import multipletests
  
from cliffs_delta import cliffs_delta

def get_cliffs_delta(data1, data2):
    d, res = cliffs_delta(data1, data2)
    return d, res

def bh_correct(p_values):
    return multipletests(p_values, method='fdr_bh')[1]

def wilcoxon_test(data1, data2):
    stat, p = wilcoxon(data1, data2)
    return p

def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def result_dict_to_list(result_dict):
    result_list = []
    human_data = result_dict["humaneval"]
    mbpp_data = result_dict["mbpp"]
    for key, value in human_data.items():
        result_list.append(value)
    for key, value in mbpp_data.items():
        result_list.append(value)
    return result_list

def get_wtl(cliff_deltas, p_values):
    win = 0
    tie = 0
    lose = 0
    for cliff_delta, p_value in zip(cliff_deltas, p_values):
        if p_value < 0.05:
            if cliff_delta < -0.147:
                win += 1
            elif cliff_delta > 0.147:
                lose += 1
            else:
                tie += 1
        else:
            tie += 1
    return win, tie, lose

    

def compare_result_to_csv(result, csv_path, wtl_csv_path):
    metrics = ["pass@1", "pass@3", "pass@5", "pass@7", "pass@10"]
    methods = list(result["pass@1"].keys())[0:6]
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            "value_type", "methods"] + metrics)
        writer.writeheader()  # 写入表头
        p_value_head_writed = False
        cliffs_delta_head_writed = False
        for method in methods:
            row = dict()
            if not p_value_head_writed:
                row["value_type"] = "p_value"
                p_value_head_writed = True
            else:
                row["value_type"] = ""
            row["methods"] = method
            for metric in metrics:
                row[metric] = result[metric][method]["wilcoxon_p"]
            writer.writerow(row)
        for method in methods:
            row = dict()
            if not cliffs_delta_head_writed:
                row["value_type"] = "cliffs_delta"
                cliffs_delta_head_writed = True
            else:
                row["value_type"] = ""
            row["methods"] = method
            for metric in metrics:
                row[metric] = result[metric][method]["cliffs_delta"]
            writer.writerow(row)

    # 统计 win, tie, lose 的数量
    with open(wtl_csv_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=[
            "Metrics"]+[metric for metric in metrics])
        writer.writeheader()  # 写入表头
        results = ["win", "tie", "lose"]
        for result_type in results:
            row = dict()
            row["Metrics"] = result_type
            for metric in metrics:
                # 获取 win, tie, lose 的数量
                num = result[metric][result_type]
                row[metric] = num
            writer.writerow(row)
        
    # with open(csv_path, mode='w', newline='') as file:
    #     writer = csv.DictWriter(file, fieldnames=[
    #         "comparison", "pass_level", "wilcoxon_p", "cliffs_delta"
    #     ])
        
    #     writer.writeheader()  # 写入表头
        
    #     # 遍历每个 "pass@" 级别的比较
    #     for pass_level, comparisons in result.items():
    #         for comparison, values in comparisons.items():
    #             # 构造每行的数据
    #             row = {
    #                 "comparison": comparison,
    #                 "pass_level": pass_level,
    #                 "wilcoxon_p": values["wilcoxon_p"],
    #                 "cliffs_delta": values["cliffs_delta"]
    #             }
    #             # 写入数据行
    #             writer.writerow(row)


def stats_results_to_csv(baseline_statis_results, combmt_statis_result, dataset ,csv_path):
    pass_titles = baseline_statis_results.keys()
    models = ["incoder-1B", "codegen-2B", "codegen2-1B", "santacoder"]
    field_names = ["methods"] + [f"{pass_title}_{model}" for model in models for pass_title in pass_titles]
    baselines = ["base", "insert_line", "comment", "output_mutation", "output_v_mutation"]
    mutants = ["mutant_1", "mutant_2", "mutant_3"]
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=field_names)
        writer.writeheader()
        base_results = dict()
        for baseline in baselines:
            row = {"methods": baseline}
            for pass_title in pass_titles:
                for model in models:
                    pass_k_model = round(baseline_statis_results[pass_title][baseline][dataset][f"passat10_{model}"], 2)
                    row_key = f"{pass_title}_{model}"
                    if baseline == "base":
                        base_results[row_key] = pass_k_model
                    # 两位百分数，体现出变化率
                    change_rate = round((pass_k_model - base_results[row_key]) / base_results[row_key] * 100, 2)
                    row[row_key] = f"{pass_k_model:.10g} ({change_rate:.2f}%)"
            writer.writerow(row)
        for mutant in mutants:
            row = {"methods": mutant}
            for pass_title in pass_titles:
                for model in models:
                    pass_k_model = round(combmt_statis_result[pass_title][mutant][dataset][f"passat10_{model}"], 2)
                    row_key = f"{pass_title}_{model}"
                    change_rate = round((pass_k_model - base_results[row_key]) / base_results[row_key] * 100, 2)
                    row[row_key] = f"{pass_k_model:.10g} ({change_rate:.2f}%)"
            writer.writerow(row)

            


def main():
    combmt_data = read_json("./dataset/pass_k_statistics_combmt.json")
    baselines_data = read_json("./dataset/pass_k_statistics_baselines.json")
    combmt_mutants = ["mutant_1", "mutant_2", "mutant_3"]
    baselines = ["output_mutation", "output_v_mutation"]
    stats_results = {}
    sigificance_results = {}
    p_values_bf_bh = []
    metrics = ["pass@1", "pass@3", "pass@5", "pass@7", "pass@10"]
    for metric in metrics:
        stats_results[metric] = {}
        sigificance_results[metric] = {}

        
        for baseline in baselines:
            result_of_baseline = baselines_data[metric][baseline]
            result_lst_of_baseline = result_dict_to_list(result_of_baseline)
            result_lst_of_baseline = [round(x, 2) for x in result_lst_of_baseline]
            stats_results[metric][baseline] = result_lst_of_baseline

        for mutant in combmt_mutants:
            result_of_combmt = combmt_data[metric][mutant]
            result_lst_of_combmt = result_dict_to_list(result_of_combmt)
            result_lst_of_combmt = [round(x, 2) for x in result_lst_of_combmt]
            stats_results[metric][mutant] = result_lst_of_combmt
        
        wilcoxon_ps = []
        cliffs_deltas = []
        for mutant in combmt_mutants:
            for baseline in baselines:
                data1 = stats_results[metric][mutant]
                # data1 = [round(x, 2) for x in data1]
                data2 = stats_results[metric][baseline]
                # data2 = [round(x, 2) for x in data2]
                wilcoxon_p = wilcoxon_test(data1, data2)
                wilcoxon_p = round(wilcoxon_p, 3)
                p_values_bf_bh.append(wilcoxon_p)
                wilcoxon_ps.append(wilcoxon_p)
                index = len(p_values_bf_bh) - 1
                # bh_p = bh_correct(wilcoxon_p)
                cliffs_delta, res = get_cliffs_delta(data1, data2)
                cliffs_delta = round(cliffs_delta, 3)
                cliffs_deltas.append(cliffs_delta)
                cliffs_delta = f"{cliffs_delta} ({res[0].upper()})"

                sigificance_results[metric][f"{mutant} vs {baseline}"] = {"wilcoxon_p": wilcoxon_p, "cliffs_delta": cliffs_delta, "p_index": index}
        wintieloss  = get_wtl(cliffs_deltas, wilcoxon_ps)
        sigificance_results[metric]["win"] = wintieloss[0]
        sigificance_results[metric]["tie"] = wintieloss[1]
        sigificance_results[metric]["lose"] = wintieloss[2]
    bh_p_values = bh_correct(p_values_bf_bh)
    bh_p_values = [round(x, 3) for x in bh_p_values]
    for metric in metrics:
        for key in list(sigificance_results[metric].keys())[0:6]:
            index = sigificance_results[metric][key]["p_index"]
            sigificance_results[metric][key]["bh_p"] = bh_p_values[index]
    write_json("./results/pass_k_stats_results.json", stats_results)
    write_json("./results/pass_k_sigificance_results.json", sigificance_results)

    compare_result_to_csv(sigificance_results, "./results/pass_k_sigificance_results_v2.csv", "./results/pass_k_sigificance_results_wtl.csv")
    stats_results_to_csv(baselines_data, combmt_data, "humaneval", "./results/humaneval_pass_k_stats_results.csv")
    stats_results_to_csv(baselines_data, combmt_data, "mbpp", "./results/mbpp_pass_k_stats_results.csv")
            
        


if __name__ == '__main__':
    main()



