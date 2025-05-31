script_path="../scripts/mutant"


sample_num=10
dataset=humaneval
# dataset=mbpp

for mutant_type in "base" "insert_line" "comment" "output_mutation" "output_v_mutation"; do
    for model_name in "incoder-1B" "santacoder" "codegen-2B" "codegen2-1B"; do
        output_folder="./results/${dataset}_${mutant_type}"
        mkdir -p $output_folder

        mutant_path="datasets/${dataset}/${mutant_type}/${dataset}_${mutant_type}.jsonl"

        output_path="${output_folder}/passat${sample_num}_$model_name"
        mkdir -p $output_path
        python ${script_path}/baseline_gen.py \
            --dataset $dataset \
            --mutant_path $mutant_path \
            --model_name $model_name \
            --output_path $output_path \
            --n_samples $sample_num
    done
done

