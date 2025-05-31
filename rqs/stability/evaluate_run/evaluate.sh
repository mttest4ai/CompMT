dataset="human-eval"
# dataset="mbpp-sanitized"
# model="incoder-1B"
# model="codegen-2B"
# model="santacoder"
# model="codegen2-1B"

# sub_folder="T01"
for sub_folder in "T02" "T04" "T06" "T10"; do

    for model in "codegen-2B" "santacoder" "incoder-1B" "codegen2-1B"; do

        output_path="../results/init_${dataset}_vner4/${sub_folder}/passat10_${model}"

        python evaluate.py \
            --output_path $output_path \
            --dataset $dataset \
            --model $model 2>&1 | tee ${output_path}/evaluate.log
    done
done

# nohup python evaluate.py \
#     --output_path $output_path \
#     --dataset $dataset \
#     --model $model > ${output_path}/evaluate.log 2>&1 &