script_path="../scripts/mutant"


sample_num=10
output_folder="./stability/results/init_human-eval_vner4"
mutant_path="${output_folder}/mutant_results_init.jsonl"
# model_name=codegen-2B
model_name=incoder-1B
# model_name=santacoder

for temperature in 0.1 0.3 0.5 0.7 0.9; do
    temp_folder=T$(echo "$temperature" | sed 's/\.//g')

    output_path="${output_folder}/${temp_folder}/passat${sample_num}_$model_name"
    mkdir -p "${output_folder}/${temp_folder}"
    mkdir -p $output_path

    python ${script_path}/generate_hysta.py \
        --mutant_path $mutant_path \
        --model_name $model_name \
        --output_path $output_path \
        --temperature $temperature \
        --n_samples $sample_num 2>&1 | tee ${output_path}/generate.log
done