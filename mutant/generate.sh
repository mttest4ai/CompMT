script_path="../scripts/mutant"


sample_num=10
output_folder="./results/init_human-eval_vner4"
mutant_path="${output_folder}/mutant_results_init.jsonl"
model_name=codegen-2B
# model_name=chatgpt
# model_name=santacoder
output_path="${output_folder}/passat${sample_num}_$model_name"
mkdir -p $output_path


# nohup python ${script_path}/generate.py \
#     --mutant_path $mutant_path \
#     --model_name $model_name \
#     --output_path $output_path \
#     --n_samples $sample_num > ${output_path}/generate.log 2>&1 &

python ${script_path}/generate.py \
    --mutant_path $mutant_path \
    --model_name $model_name \
    --output_path $output_path \
    --n_samples $sample_num 2>&1 | tee ${output_path}/generate.log 2>&1 &
