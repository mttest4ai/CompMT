# dataset="human-eval"
dataset="mbpp-sanitized"
# model="incoder-1B"
model="chatgpt"
# model="santacoder"
# model="codegen2-1B"
output_path="../results/init_${dataset}_vner4/passat10_${model}"

python evaluate.py \
    --output_path $output_path \
    --dataset $dataset \
    --model $model 2>&1 | tee ${output_path}/evaluate.log

# nohup python evaluate.py \
#     --output_path $output_path \
#     --dataset $dataset \
#     --model $model > ${output_path}/evaluate.log 2>&1 &