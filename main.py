import ast
import json
import os
import openai
import random
import time
import atexit
from datetime import datetime, timedelta
import argparse
from tqdm import tqdm
from collections import OrderedDict, Counter
from tool import *



def query(message: dict, key: str, temperature: float, backbone: str, prompt: str, sc_num: int):
    '''
    This function is used to query OpenAI for solutions.

    Args:
        data: a dict containing the question and answer
        key: the OpenAI API key
        temperature: temperature
        backbone: ChatGPT or GPT-4
        prompt: prompting method
        sc_num: the number of self-consistency samples

    Returns:
        completions: a list containing the CoT solution
    '''    
    if backbone == 'gpt4':
        model_name = 'gpt-4'
    elif backbone == 'chatgpt':
        model_name = 'gpt-3.5-turbo'

    start_time = time.time()
    wait_time = min(sc_num * 40, 200)
    request_timeout = 30 if prompt == 'standard' else sc_num * 20
    solution = None
    while solution is None:
        try:
            solution = openai.ChatCompletion.create(
                api_key=key,
                model=model_name,
                max_tokens=500,
                messages=message,
                temperature=temperature,
                n=sc_num,
                request_timeout=request_timeout)
        except Exception as e:
            print(e)
            sleep_time = random.uniform(3, 5)
            time.sleep(sleep_time)

            if time.time() - start_time > wait_time:
                print("Time out")
                raise e

    completions = [choice['message']['content'] for choice in solution['choices']]
    return completions


def sc_query(data: dict, key: str, temperature: float, prompt: str, sc_num: int, backbone: str):
    '''
    This function is used to query OpenAI for answers in classification tasks.
    We also use majority voting to select the final answer if we have multiple self-consistency samples.

    Args:
        data: a dict containing the question and answer
        key: the OpenAI API key
        prompt: prompting method
        temperature: 0 for greedy decoding. We set it to 0.5 for self-consistency samples.
        sc_num: the number of self-consistency samples
        backbone: ChatGPT or GPT-4

    Returns:
        to_dump_data: a dict containing the question, answer, the final answer and other information
    '''

    classes = [f"\\boxed{{{s.strip()}}}"  for s in ast.literal_eval(data['classes'])]
    prompt_message = f"{data['question']}\nclasses: {classes}"
    if prompt == 'cot':
        prompt_message += "\n\nLet’s think step by step"
    elif prompt == 'instruct':
        prompt_message += """\n\nLet’s think step by step
1. separate instruction and question
2. map target in question under instruction. Express mapper as {target->value_of_target} form in place of question.
3. Solve question.  Put your answer in \\boxed{}."""
    query_message = [{"role": "user", "content": prompt_message}]

    try:
        solutions = query(query_message, key, temperature, backbone, prompt, sc_num)
    except Exception as e:
        raise e
    
    classes = [s.strip() for s in ast.literal_eval(data['classes'])]    
    final_answers = [extract_classes_turbo(s, classes) for s in solutions]

    filtered_answers = list(filter(lambda x: x is not None, filter(lambda x: 'Ambiguous' != x, final_answers)))
    if filtered_answers:
        count = Counter(filtered_answers)
        majority_ans = count.most_common(1)[0][0]
    else:
        majority_ans = None

    # === dump data ===
    to_dump_data = OrderedDict({
        'index': data['index'], 
        'answer': classes[data['answer_index']],
        'majority_ans': majority_ans,
        'final_answers': final_answers,
        'question': data['question'],
        'generated': solutions
    })
    return to_dump_data


def getDataset(dataset_name):
    if dataset_name == 'redefine':
        dataset = jsonlines_load('data/isp-redefine.jsonl')
    elif dataset_name == 'linguistic':
        dataset = jsonlines_load('data/linguistic_redefine.jsonl')
    elif dataset_name == 'original':
        dataset = jsonlines_load('data/original.jsonl')
    return dataset


def getArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=-1)
    parser.add_argument('--dataset', type=str, choices=[
                        'redefine', 'linguistic', 'original'], default='gsm8k')
    parser.add_argument('--backbone', type=str,
                        choices=['chatgpt', 'gpt4'], default='chatgpt')
    parser.add_argument('--temperature', type=float, default=0.5)
    parser.add_argument('--prompt', type=str, choices=['standard', 'cot','instruct'], default='standard')
    parser.add_argument('--sc_num', type=int, default=1,
                        help='Self-consistency samples. 1 indicates greedy decoding')
    parser.add_argument('--output_dir', type=str, default='output/')
    parser.add_argument('--key', type=str, default='sk-', required=True)

    args = parser.parse_args()

    start_index = args.start
    end_index = args.end
    dataset_name = args.dataset
    backbone = args.backbone
    temperature = args.temperature
    prompt = args.prompt
    sc_num = args.sc_num
    output_dir = args.output_dir
    key = args.key
    return start_index, end_index, dataset_name, backbone, temperature, prompt, sc_num, output_dir, key


def get_save_path(output_dir, backbone, dataset_name, prompt, sc_num, start_index, end_index):
    output_path = os.path.join(output_dir, f'{backbone}/')

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    dt_string = datetime.now().strftime("%m_%d_%H_%M")
    save_path = os.path.join(output_path,
                             f'{dataset_name}_{prompt}_sc{sc_num}_s{start_index}_e{end_index}_{dt_string}.jsonl')
    return save_path


def get_slice_dataset(dataset, start_index, end_index):
    total_num = len(dataset)
    print('total data: ', total_num)
    if end_index == -1:
        end_index = total_num

    if end_index > total_num:
        end_index = total_num

    tasks = dataset[start_index:end_index]
    print('Current total tasks: ', len(tasks))
    return tasks

def wrap_up(start_time, unfinished_tasks):
    print()
    end_time = time.time()
    print('Finish at time: ', time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()))
    print(f'Time used: {timedelta(seconds=end_time - start_time)}')

    if len(unfinished_tasks) > 0:
        print('Unfinished tasks: ')
        print(*unfinished_tasks, sep="\n")

if __name__ == '__main__':
    start_index, end_index, dataset_name, backbone, temperature, prompt, sc_num, output_dir, key = getArgs()

    print('=' * 25)
    print(f'{backbone=} {temperature=} {prompt=} {sc_num=} {dataset_name=} {start_index=} {end_index=} {output_dir=}')
    start_time = time.time()
    print('Current time: ', time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()))

    dataset = getDataset(dataset_name)
    tasks = get_slice_dataset(dataset, start_index, end_index)

    save_path = get_save_path(
        output_dir, backbone, dataset_name, prompt, sc_num, start_index, end_index)


    # === run experiments ===
    unfinished_tasks = []
    atexit.register(wrap_up, start_time, unfinished_tasks)
    for i, task in enumerate(tqdm(tasks)):
        task_start_time = time.time()
        ans = None
        while ans is None:
            try:
                ans = sc_query(
                    task, key=key, temperature=temperature,
                    prompt=prompt, sc_num=sc_num, backbone=backbone)
            except Exception as e:
                print(f"[#{task['index']} Task]", e)
                unfinished_tasks.append(task)
                break
        else:
            with open(save_path, "a+") as fout:
                fout.write(json.dumps(ans)+'\n')
            # sleep_time = random.uniform(3,5)
            sleep_time = 5
            time.sleep(sleep_time)
               
    print('Done')
