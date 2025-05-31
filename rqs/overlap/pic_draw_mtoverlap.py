import venn
import json
import os
import time
import matplotlib.pyplot as plt
import matplotlib

# plt.rcParams['font.size'] = 26

pic_font_size = 25

def read_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)
    
def write_json(data, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=3)

def write_text(string_text, file_path):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(string_text)



if __name__ == "__main__":
    datasets = ["humaneval", "mbpp-sanitized"]
    models = ["passat10_incoder-1B","passat10_codegen-2B", "passat10_codegen2-1B",  "passat10_santacoder"]
    model_to_names = {
        "passat10_incoder-1B": "Incoder",
        "passat10_codegen-2B": "CodeGen",
        "passat10_codegen2-1B": "CodeGen2",
        "passat10_santacoder": "Santacoder",
    }
    baseline_types = ["base", "comment", "insert_line", "output_mutation", "output_v_mutation"]
    mutant_types = ["mutant_1_item", "mutant_2_item", "mutant_3_item"]
    pic_font_size = 30
    title_font_size = 30

    fig = plt.figure(figsize=(12, 12))
    axes = [fig.add_subplot(221), fig.add_subplot(222), fig.add_subplot(223), fig.add_subplot(224)]

    # 对每个模型，合并两个数据集上的结果后画 Venn 图
    for i, model in enumerate(models):
        combined_mutant_1 = set()
        combined_mutant_2 = set()
        combined_mutant_3 = set()

        for dataset in datasets:
            combmt_result = read_json(f"./combmt/{dataset}_static_result.json")
            model_result = combmt_result[model]["passed"]
            combined_mutant_1.update(model_result["mutant_1_item"])
            combined_mutant_2.update(model_result["mutant_2_item"])
            combined_mutant_3.update(model_result["mutant_3_item"])

        overlap = venn.get_labels(
            [combined_mutant_1, combined_mutant_2, combined_mutant_3],
            fill=["number"]
        )

        ax = venn.venn3_ax(
            axes[i], overlap,
            names=["MR1", "MR2", "MR3"],
            legend=False,
            fontsize=pic_font_size
        )
        ax.set_title(f"Overlap on {model_to_names[model]}", y=-0.07, fontdict={'fontsize': title_font_size})

    plt.tight_layout()
    plt.savefig(f"./results/combined_MR_overlap.pdf")
    plt.close()

    # for dataset in datasets:
    #     fig = plt.figure(figsize=(12, 12))
    #     ax1 = fig.add_subplot(221)
    #     ax2 = fig.add_subplot(222)
    #     ax3 = fig.add_subplot(223)
    #     ax4 = fig.add_subplot(224)
    #     ax_list = [ax1, ax2, ax3, ax4]
    #     combmt_result = read_json(f"./combmt/{dataset}_static_result.json")
    #     # baselines_result = read_json(f"./baselines/{dataset}_static_result.json")
    #     for i in range(4):
    #         model = models[i]
            
    #         combmt_model_result = combmt_result[model]["passed"]
    #         mutant_1_passed = combmt_model_result["mutant_1_item"]
    #         mutant_2_passed = combmt_model_result["mutant_2_item"]
    #         mutant_3_passed = combmt_model_result["mutant_3_item"]

    #         mutant_overlap = venn.get_labels([mutant_1_passed, mutant_2_passed, mutant_3_passed], fill=["number"])        
    #         ax = venn.venn3_ax(ax_list[i], mutant_overlap, names=["MR1", "MR2", "MR3"], legend=False, fontsize=pic_font_size)
    #         # method_overlap = venn.get_labels([combmt_all_passeds, *baselines_passed], fill=["number"])
    #         # ax = venn.venn6_ax(ax_list[i], method_overlap, names=["CombMT", "Base", "Comment", "InsertLine", "PPM-T", "PPM-V"], legend=False, fontsize=pic_font_size)
            
    #         ax_title = f"Overlap On {model_to_names[model]}"
    #         ax.set_title(ax_title, y=-0.12, fontdict={'fontsize':title_font_size})
    #     plt.tight_layout()
    #     plt.savefig(f"./results/{dataset}_MR_overlap.pdf")
    #     plt.close()


