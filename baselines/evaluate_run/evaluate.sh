dataset="mbpp"
# dataset="mbpp-sanitized_oneshot"
# model="incoder-1B"
# model="santacoder"
model="codegen-2B"
# mutant_type="output_v_mutation"
# output_path="../results/${dataset}_${mutant_type}/passat10_${model}"


# python evaluate.py \
#     --output_path $output_path \
#     --dataset $dataset \
#     --model $model \
#     --mutant_type $mutant_type 

# nohup python evaluate.py \
#     --output_path $output_path \
#     --dataset $dataset \
#     --model $model \
#     --mutant_type $mutant_type > ${output_path}/evaluate.log 2>&1 &


for mutant_type in "base" "insert_line" "comment" "output_mutation" "output_v_mutation"; do # "insert_line" "comment" "output_mutation" "output_v_mutation"; do
    output_path="../results/${dataset}_${mutant_type}/passat10_${model}"
    # nohup python evaluate.py \
    #     --output_path $output_path \
    #     --dataset $dataset \
    #     --model $model \
    #     --mutant_type $mutant_type > ${output_path}/evaluate.log 2>&1 &
    python evaluate.py \
        --output_path $output_path \
        --dataset $dataset \
        --model $model \
        --mutant_type $mutant_type 2>&1 | tee ${output_path}/evaluate.log
done