import os
import sys
import regex
from tqdm import tqdm
from collections import OrderedDict

from tool import *
from mapping import LINGUISTIC_WRONG_FROM_ORIGINAL

linguistic_output = jsonlines_load("output/chatgpt/linguistic_sc5_s0_e-1_11_18_22_01.jsonl")
rating_output = jsonlines_load("output/chatgpt/ratingf_sc5_s0_e-1_11_26_00_10 copy.jsonl")


swap_dict = {}
for data in rating_output:
    swap_dict[f"{data['from']}->{data['to']}"] = data['index']

mapping = []
for data in tqdm(linguistic_output):
    words = regex.search(r'[a-z]+ and [a-z]+', data['question'])
    if not words:
        continue
    words = words[0].split(" and ")

    max_num = 0
    for w in words:
        num = len(regex.findall(w, data['question']))
        if num > max_num:
            max_num = num 
            target_word = w
        elif num and num == max_num:
            print(f"[#{data['index']} Task] same number of word in quesiton")
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