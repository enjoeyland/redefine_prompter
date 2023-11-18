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
    prd = [x[0][6:-1] for x in regex.finditer("boxed{[1-9a-zA-Z]+}", solution)]
    if prd:
        return prd[-1]
    
    prd = [x[0] for x in regex.finditer(r'[\d\.,]+', solution) if regex.search(r'\d', x[0])]
    prd = list(filter(lambda x: x in classes, prd))
    if prd:
        return prd[-1]
    
    for c in classes:
        if regex.findall(c, solution):
            prd = c
            return prd
    return None    


def extract_num_turbo(solution: str):
    ans = solution.strip().split('\n')[-1].replace('So the answer is ', '')
    prd = [x[0] for x in regex.finditer(
        r'[\d\.,]+', ans) if regex.search(r'\d', x[0])]
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