import json
import matplotlib.pyplot as plt

# 红蓝配色（学术常用，来自matplotlib默认ColorCycle）
red_color = "#F8766D"
blue_color = "#00BFC4"
font_size = 20

# 读取数据
with open("./results/pass_k_statistics_combmt_medium.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 所有pass@k的key（确保按顺序）
pass_ks = ["pass@1", "pass@3", "pass@5", "pass@7", "pass@10"]

# 提取方法名
all_methods = [entry["method"] for entry in data["pass@1"]]  # 用 pass@1 中的顺序
mutants = {"mutant_1", "mutant_2", "mutant_3"}

method_name_dict = {
    "base": "Base",
    "insert_line": "Insert Line",
    "comment": "Comment",
    "output_mutation": "PPM-T",
    "output_v_mutation": "PPM-V",
    "mutant_1": "MR1",
    "mutant_2": "MR2",
    "mutant_3": "MR3"
}

# 开始画图
fig, axs = plt.subplots(1, len(pass_ks), figsize=(20, 5), sharey=True)

for i, k in enumerate(pass_ks):
    ax = axs[i]
    results = data[k]
    
    method_names = []
    method_data = []
    colors = []

    for entry in results:
        method = entry["method"]
        method_names.append(method)
        method_data.append(entry["results"])
        colors.append(red_color if method in mutants else blue_color)
    
    # 画箱线图
    bp = ax.boxplot(
        method_data,
        patch_artist=True,
        boxprops=dict(linewidth=0.8),
        medianprops=dict(color='black', linewidth=1.2),
        whiskerprops=dict(linewidth=0.8),
        capprops=dict(linewidth=0.8),
        flierprops=dict(marker='o', markersize=3, linewidth=0.5)
    )
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    method_labels = [method_name_dict[method] for method in method_names]
    ax.set_xticks(range(1, len(method_names)+1))
    ax.set_xticklabels(method_labels, rotation=45, ha='right', fontsize=font_size-5)
    ax.set_title(k, fontsize = font_size)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.tick_params(axis='y', labelsize=font_size-5)

# fig.suptitle("Pass@k Results of Different Methods", fontsize=14)
fig.text(-0.01, 0.5, 'Pass@K', va='center', rotation='vertical', fontsize=font_size-5)
fig.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("pass_k_boxplots.pdf", bbox_inches="tight")
plt.show()
