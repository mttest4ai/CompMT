import matplotlib.pyplot as plt
import numpy as np
import json

def read_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

# 创建数据
x = [0.1, 0.3, 0.5, 0.7, 0.9]
# y_list = [
#     [3, 3, 3, 3, 3],  # pass@1
#     [2, 2, 2, 2, 2],  # pass@10
#     [4, 4, 4, 4, 4],  # pass@1
#     [1, 2, 1, 2, 1],  # pass@10
#     [4, 3, 4, 3, 4],  # pass@1
#     [2, 1, 2, 1, 2],   # pass@10
#     [3, 3, 3, 3, 3],  # pass@1
#     [2, 2, 2, 2, 2],  # pass@10
#     [4, 4, 4, 4, 4],  # pass@1
#     [1, 2, 1, 2, 1],  # pass@10
#     [4, 3, 4, 3, 4],  # pass@1
#     [2, 1, 2, 1, 2]   # pass@10
# ]

fontsize = 20
tick_size = 16

colors = {
    "pass@1": (228 / 255, 26 / 255, 28 / 255),   # 红色
    "pass@10": (55 / 255, 126 / 255, 184 / 255)  # 蓝色
}

linestyles = {
    "mbpp-sanitized": 'solid',
    "human-eval": 'dashed'
}

markers = {
    "mt_1": 'o',
    "mt_2": 's',
    "mt_3": '^'
}

models = ["passat10_incoder-1B", "passat10_codegen-2B", "passat10_codegen2-1B", "passat10_santacoder"]
model_to_names = {
    "passat10_incoder-1B": "Incoder",
    "passat10_codegen-2B": "CodeGen",
    "passat10_codegen2-1B": "CodeGen2",
    "passat10_santacoder": "Santacoder",
}
mutant_types = ["mt_1", "mt_2", "mt_3"]
mutant_types_to_keyname = {"mt_1": "MR1", "mt_2": "MR2", "mt_3": "MR3"}
temperature_lst = ["T01", "T03", "T05", "T07", "T09"]
x = np.arange(0, 1, 0.2)

datasets = ["mbpp-sanitized", "human-eval"]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes = axes.flatten()

for model_id, ax in enumerate(axes):
    model = models[model_id]

    for mt_type in mutant_types:
        for dataset in datasets:
            pass1_lst = []
            pass10_lst = []
            for temperature in temperature_lst:
                output_path = f"./results/init_{dataset}_vner4/{temperature}/{model}/run_results"
                pass1 = read_json(f"{output_path}/{mt_type}_pass_at_1.json")["pass@k"]
                pass10 = read_json(f"{output_path}/{mt_type}_pass_at_10.json")["pass@k"]
                pass1_lst.append(pass1)
                pass10_lst.append(pass10)

            ax.plot(
                x, pass1_lst,
                color=colors["pass@1"],
                linestyle=linestyles[dataset],
                marker=markers[mt_type],
                lw=2
            )
            ax.plot(
                x, pass10_lst,
                color=colors["pass@10"],
                linestyle=linestyles[dataset],
                marker=markers[mt_type],
                lw=2
            )

    ax.set_xlabel('Temperature', fontsize=fontsize)
    ax.set_ylabel('Pass@k', fontsize=fontsize)
    ax.set_xticks(np.arange(0, 1, 0.2))
    ax.set_yticks(np.arange(0, 0.5, 0.1))
    ax.tick_params(axis='both', labelsize=tick_size)
    ax.set_title(f'{model_to_names[model]}', fontsize=fontsize)
    ax.yaxis.grid(True, linestyle='--', color='gray')
    ax.xaxis.grid(False)

# 调整布局，图例改为文字说明
plt.tight_layout()

# 保存图
plt.savefig('both_datasets_passk_plot_clean.pdf', dpi=300, bbox_inches='tight')
plt.show()

