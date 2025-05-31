
script_path="../scripts/mutant"
data_folder="../datasets/benchmarks"

seed_benchmark_name="human-eval"
seed_benchmark_path="$data_folder/humaneval-py-transform.json"

# seed_benchmark_name="mbpp-sanitized"
# seed_benchmark_path="$data_folder/mbpp-py-reworded.json"

comb_benchmark_path="$data_folder/mbpp/mbpp-unsanitized.jsonl"
# comb_benchmark_path="$data_folder/odex/odex_filtered_data.jsonl"
current_time=vner4 # $(date "+%Y.%m.%d-%H.%M.%S")

mkdir -p "./results"
output_path="./results/init_${seed_benchmark_name}_${current_time}"
mkdir -p $output_path

python ${script_path}/mt_init.py \
    --seed_benchmark_path $seed_benchmark_path \
    --comb_benchmark_path $comb_benchmark_path \
    --output_path $output_path

