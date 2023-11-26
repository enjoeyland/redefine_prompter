import json
import re
import regex
import func_timeout
from typing import Union
import random


def jsonlines_load(fname: str):
    with open(fname, 'r') as f:
        return [json.loads(line) for line in f]


def jsonlines_dump(fname: str, data: Union[dict, list]):
    try:
        with open(fname, 'a+') as f:
            if isinstance(data, dict):
                f.write(json.dumps(data)+'\n')
            elif isinstance(data, list):
                for d in data:
                    f.write(json.dumps(d)+'\n')

    except (FileNotFoundError, FileExistsError) as e:
        print(f'Error: {e}')
        print(f'Could not write to {fname}')


def extract_classes_turbo(solution: str, classes: list):
    max_num = 0
    prd = None
    for c in classes:
        num = len(regex.findall(c, solution))
        if num > max_num:
            max_num = num 
            prd = c
        elif num and num == max_num:
            prd = 'Ambiguous'
    if prd:
        return prd
    return None    

def extract_rate_turbo(solution: str, expect: list):
    if not regex.search(r'\d', solution):
        return None
    try:
        prd = regex.search(r'\d+', regex.search(r'\d.+ '+expect, solution.lower())[0])[0]
        return int(prd)
    except:            
        return 15

def extract_num_turbo(solution: str):
    ans = solution.strip().split('\n')[-1].replace('So the answer is ', '')
    prd = [x[0] for x in regex.finditer(r'[\d\.,]+', ans) if regex.search(r'\d', x[0])]
    if len(prd) > 2:
        prd = prd[-1]
    elif len(prd):
        prd = prd[0]
    else:
        prd = None
    try:
        prd = float(prd.replace(',', '').rstrip('.')) if prd else prd
    except:
        prd = None
    return prd