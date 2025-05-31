import numpy as np
import matplotlib.pyplot as plt
import json


def read_jsonl(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line.strip()) for line in f]
    
    

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

def distribution_dict_to_list(dict):
    return [dict[str(i)] for i in range(1,11)]

if __name__ == "__main__":
    
    pass_num = range(1, 11)

    baseline_data = read_json("baseline_pass_num_statistics.json")
    combmt_data = read_json("combmt_pass_num_statistics.json")

    base_distr = distribution_dict_to_list(baseline_data["base"])
    comment_distr = distribution_dict_to_list(baseline_data["comment"])
    insert_distr = distribution_dict_to_list(baseline_data["insert_line"])
    ppm_t_distr = distribution_dict_to_list(baseline_data["output_mutation"])
    ppm_v_distr = distribution_dict_to_list(baseline_data["output_v_mutation"])
    mutant_1_distr = distribution_dict_to_list(combmt_data["mutant_1"])
    mutant_2_distr = distribution_dict_to_list(combmt_data["mutant_2"])
    mutant_3_distr = distribution_dict_to_list(combmt_data["mutant_3"])

    # datas = [base_distr, insert_distr, comment_distr, ppm_t_distr, ppm_v_distr, mutant_1_distr, mutant_2_distr, mutant_3_distr]
    # names = ["Base", "Insert_line", "Comment", "PPM-T", "PPM-V", "MR1", "MR2", "MR3"]
    # datas = [ppm_t_distr, ppm_v_distr, mutant_1_distr, mutant_2_distr, mutant_3_distr]
    # names = ["PPM-T", "PPM-V", "MR1", "MR2", "MR3"]
    datas = [mutant_1_distr, mutant_2_distr, mutant_3_distr]
    names = ["MR1", "MR2", "MR3"]

    font_size = 35
    bar_width = 0.5
    x_spacing = 2  # 每个横坐标之间的间距
    x = np.arange(len(pass_num)) * x_spacing  # 放宽横坐标
    plt.figure(figsize=(16, 8))  # 调大图片尺寸

    num_bars = len(datas)
    total_width = num_bars * bar_width

    for i, data in enumerate(datas):
        name = names[i]
        offset = i * bar_width - total_width/2  + bar_width/2 
        bars = plt.bar(x + offset, data, width=bar_width, label=name)
        for bar in bars:
            height = bar.get_height()
            if height == 0:
                continue
            plt.text(
                bar.get_x() + bar.get_width() / 2,  # X坐标：柱子中间
                height,                             # Y坐标：柱子顶部
                f'{int(height)}',                    # 标签内容，保留1位小数
                ha='center', va='bottom', fontsize=font_size-11  # 水平居中，垂直在底部
            )
    plt.xticks(x, pass_num, fontsize=font_size)
    plt.yticks(fontsize=font_size)
    plt.xlabel('Pass Number', fontsize=font_size)
    plt.ylabel('Count', fontsize=font_size)
    plt.legend(fontsize=font_size)
    plt.tight_layout()
    plt.savefig("./pass_num_distribution.pdf", bbox_inches='tight')



