import ast
import json
import os
import openai
import random
import time
from datetime import datetime, timedelta
import argparse
from tqdm import tqdm
from collections import OrderedDict, Counter
from tool import *



def query(data: dict, key: str, temperature: float, backbone: str, sc_num: int):
    '''
    This function is used to query OpenAI for solutions.

    Args:
        data: a dict containing the question and answer
        key: the OpenAI API key
        temperature: temperature
        backbone: ChatGPT or GPT-4

    Returns:
        completions: a list containing the CoT solution
    '''    
    classes = [f"\\boxed{{{s.strip()}}}"  for s in ast.literal_eval(data['classes'])]
    prompt_message = f"{data['question']}\nclasses: {classes}"
    query_message = [{"role": "user", "content": prompt_message}]

    if backbone == 'gpt4':
        model_name = 'gpt-4'
    elif backbone == 'chatgpt':
        model_name = 'gpt-3.5-turbo'

    start_time = time.time()
    wait_time = min(sc_num * 12, 200)
    cot_solution = None
    while cot_solution is None:
        try:
            cot_solution = openai.ChatCompletion.create(
                api_key=key,
                model=model_name,
                max_tokens=500,
                messages=query_message,
                temperature=temperature,
                n=sc_num,
                request_timeout = 30)
        except Exception as e:
            print(e)
            sleep_time = random.uniform(3, 5)
            time.sleep(sleep_time)

            if time.time() - start_time > wait_time:
                print("Time out")
                raise e

    completions = [choice['message']['content'] for choice in cot_solution['choices']]
    return completions


def sc_query(data: dict, key: str, temperature: float, sc_num: int, backbone: str):
    '''
    This function is used to query OpenAI for answers in classification tasks.
    We also use majority voting to select the final answer if we have multiple self-consistency samples.

    Args:
        data: a dict containing the question and answer
        key: the OpenAI API key
        temperature: 0 for greedy decoding. We set it to 0.5 for self-consistency samples.
        sc_num: the number of self-consistency samples
        backbone: ChatGPT or GPT-4

    Returns:
        to_dump_data: a dict containing the question, answer, the final answer and other information
    '''
    classes = [s.strip() for s in ast.literal_eval(data['classes'])]

    try:
        solutions = query(
            data, key, temperature, backbone, sc_num)
    except Exception as e:
        raise e
    
    final_answers = [extract_classes_turbo(s, classes) for s in solutions]

    count = Counter(final_answers)
    majority_ans = count.most_common(1)[0][0]

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
    parser.add_argument('--sc_num', type=int, default=1,
                        help='Self-consistency samples. 1 indicates greedy decoding')
    parser.add_argument('--output_dir', type=str, default='output/')
    parser.add_argument(
        '--key', type=str, default='sk-', required=True)

    args = parser.parse_args()

    start_index = args.start
    end_index = args.end
    dataset_name = args.dataset
    temperature = args.temperature
    backbone = args.backbone
    sc_num = args.sc_num
    output_dir = args.output_dir
    key = args.key
    return start_index, end_index, dataset_name, temperature, backbone, sc_num, output_dir, key


def get_save_path(output_dir, backbone, dataset_name, sc_num, start_index, end_index):
    output_path = os.path.join(output_dir, f'{backbone}/')

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    dt_string = datetime.now().strftime("%m_%d_%H_%M")
    save_path = os.path.join(output_path,
                             f'{dataset_name}_sc{sc_num}_s{start_index}_e{end_index}_{dt_string}.jsonl')
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


if __name__ == '__main__':
    start_index, end_index, dataset_name, temperature, backbone, sc_num, output_dir, key = getArgs()

    print('=' * 25)
    start_time = time.time()
    print('Current time: ', time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()))

    dataset = getDataset(dataset_name)
    tasks = get_slice_dataset(dataset, start_index, end_index)

    save_path = get_save_path(
        output_dir, backbone, dataset_name, sc_num, start_index, end_index)

    # === run experiments ===
    unfinished_tasks = []
    for i, task in enumerate(tqdm(tasks)):
        task_start_time = time.time()
        ans = None
        while ans is None:
            try:
                ans = sc_query(
                    task, key=key, temperature=temperature,
                    sc_num=sc_num, backbone=backbone)
            except Exception as e:
                print(f'[#{i} Task]', e)
                unfinished_tasks.append(task)
                break
        else:
            with open(save_path, "a+") as fout:
                fout.write(json.dumps(ans)+'\n')
            # sleep_time = random.uniform(3,5)
            sleep_time = 5
            time.sleep(sleep_time)
               
    print()
    end_time = time.time()
    print('Finish at time: ', time.strftime(
        "%Y-%m-%d %H:%M:%S", time.localtime()))
    print(f'Time used: {timedelta(seconds=end_time - start_time)}')

    if len(unfinished_tasks) > 0:
        print('Unfinished tasks: ')
        print(*unfinished_tasks, sep="\n")

    print('Done')
