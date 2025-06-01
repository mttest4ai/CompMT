# CompMT: Compositional Metamorphic Testing

This is the source code for the paper "Functional Composition-based Metamorphic Testing for Evaluating Code Generation Models."

Codes in this repository are used under the environment of `Python 3.8.18`.

## Prepare dataset
For seed benchmarks, we use the processed versions in https://github.com/SeekingDream/PPM/tree/master/workdir/Dataset, please download the file `humaneval-py-transform.json` and `mbpp-py-reworded.json` to the folder `datasets/benchmarks`

For the dataset used as a problem pool, please download the MBPP dataset from https://github.com/google-research/google-research/tree/master/mbpp to the folder `datasets/benchmarks` and get mbpp-unsanitized through 
```bash
python mbpp_div.py
```

## Get Mutated Problems and Generate Code
The next steps to construct the pool of programming problems, identify suitable inserted problems and get mutated prompts. Enter folder `mutant` and run the following command:
```bash
bash init.sh
```
You can adjust the choice of seed benchmark by changing the parameter `seed_benchmark_name`.

Then, you can run the following command to generate the code:
```bash
bash generate.sh
```
You can modify the parameters in `generate.sh` according to your needs, such as the code model and generation rounds.

## Violation Detect
The next step is to check the correctness via metamorphic testing. Go to folder `evaluate/evaluate_run` and run the following command
```bash
bash evaluate.sh
```
Then, get the Pass@k result by running the following command
```bash
cd ../
python pass_k.py
```

## Research Questions
This project investigates the effectiveness of Compositional Metamorphic Testing (CompMT) through a series of empirical studies designed to answer the following research questions (RQs). All experiments and analyses related to these RQs are organized in the `rqs/` directory. Each subfolder corresponds to a specific RQ and includes the relevant scripts, data.

**RQ1: How realistic and human-like are the programming problems produced by our mutation approach?**

We put our manual experiment results in folder `rqs/natureless/results`

To get the statistics for the artificial experiment, please run the following code.
```bash
cd rqs/natureless
python static.py
python getresult.py
```

**RQ2: How effective is our method in revealing the limitations and errors of code generation models?**

For baseline question generation, we used the PPM implementation code (https://github.com/SeekingDream/PPM) and saved the generated questions in the `baselines/datasets` directory. You can run the following code to obtain the pass@k results.

```bash
# generate code
cd baselines
bash generate.sh
# get evaluation result
cd evaluate_run
bash evaluate.sh
# get pass@k and statistics result
cd ../
python pass_k.py
python pass_statistics.py
```

To obtain the boxplot results in our article, run the following command:
```bash
cp evaluate/results/pass_k_statistics_combmt.json rqs/effectiveness/dataset
cp baselines/results/pass_k_statistics_baselines.json rqs/effectiveness/dataset
cd rqs/effectiveness
python medium.py
python box.py
```

If you want to get the results of the statistical analysis, you can run the following:
```bash
cd rqs/effectiveness
python statistic.py
```

**RQ3: How does the overlap between our method and the baselines, as well as among our method’s three MRs, reflect differences in the testing perspectives of these methods?**

To obtain the result of two types of overlap, you can run the following:
```bash
python get_overlap.py
python pic_draw_baseoverlap.py
python pic_draw_mtoverlap.py
```

**RQ4: How stable is our method when varying the temperature parameter of the code generation models?**

For the stability experiments, the first step is to generate model outputs under different temperature settings. You can do this by running the following command:
```bash
cd rqs
bash generate.sh
```

Next, you can run the following code to get the test results
```bash
cd rqs/stability/evaluate_run
bash evaluate.sh
```
Then, run the following code to get the statistical results table:
```bash
cd rqs/stability
python pass_k.py
python tem_pic_both.py
```

## Discussions
Discussion **Diversity in Generated Programming Problems**:
```bash
cd discussions/diversity
python diversity.py
python diversity_table.py
```

Discussion **Effectiveness of Our Method on Online LLMs**:

Refer to the steps for generating code, set `model_name = chatgpt`, and generate code and evaluation. To obtain the experimental results, run the following code:
```bash
cd discussions/gpt_result
python statis_2_csv.py
```
Discussion **Distribution of Successful Generations**:
```bash
cd discussions/distribution
python statistics.py
python drawbar.py
```