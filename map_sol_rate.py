import regex
import argparse
from tqdm import tqdm
from collections import OrderedDict

from tool import *
from mapping_index import LINGUISTIC_WRONG_FROM_ORIGINAL


parser = argparse.ArgumentParser()
parser.add_argument('--linugistic_path', type=str, required=True)
parser.add_argument('--rating_path', type=str, required=True)
args = parser.parse_args()
linugistic_path = args.linugistic_path
rating_path = args.rating_path

linguistic_output = jsonlines_load(linugistic_path)
rating_output = jsonlines_load(rating_path)


swap_dict = {}
for data in rating_output:
    swap_dict[f"{data['from']}->{data['to']}"] = data['index']

mapping = []
for data in tqdm(linguistic_output):
    if data['question'].startswith('Swap'):
        words = regex.search(r'[a-z]+ and [a-z]+', data['question'])
        if not words:
            continue
        words = words[0].split(" and ")
    
    elif data['question'].startswith('Redefine') and "lawful" in data['question']:            
        words = ("unlawful", "lawful")

    elif data['question'].startswith('Redefine'):
        words = regex.search(r'[a-z]+ as [a-z]+', data['question'])
        if not words:
            continue
        words = words[0].split(" as ")
    else:
        continue

    max_num = 0
    for w in words:
        num = len(regex.findall(f" {w}", data['question']))
        if num > max_num:
            max_num = num 
            target_word = w
        elif num and num == max_num:
            print(f"[#{data['index']} Task] same number of word in quesiton")
            continue
    try:
        idx = swap_dict[f"{target_word}->{words[1-words.index(target_word)]}"]
    except:
        print(f"[#{data['index']} Task] wrong swap {target_word}->{words[1-words.index(target_word)]}")
        continue

    
    mapping.append(OrderedDict({
        'index': data['index'], 
        'original': data['index'] not in LINGUISTIC_WRONG_FROM_ORIGINAL,
        'answer': data['answer'],
        'majority_ans': data['majority_ans'],
        'avg_rate': rating_output[idx]['avg_rate'],
        's_final_answers': data['final_answers'],
        'r_index': rating_output[idx]['index'], 
        'r_final_answers': rating_output[idx]['final_answers'],
    }))

jsonlines_dump("output/chatgpt/mapping.jsonl", mapping)