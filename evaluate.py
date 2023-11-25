import os
import argparse
from tool import *
from mapping import *

def get_save_path(path):
    path = os.path.normpath(path).split(os.sep)
    filename, extension = os.path.splitext(path[-1])
    save_path = os.path.join(*path[:-1],f"{filename}_wrong{extension}")
    return save_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=str, required=True)
    parser.add_argument('--remove_mapping_index_variable', type=str, required=False)
    parser.add_argument('--wrong', action='store_true')
    args = parser.parse_args()

    input_path = args.input_path
    mapping_index_variable = args.remove_mapping_index_variable
    wrong = args.wrong

    output_data = jsonlines_load(input_path)
    mapping_index = []
    if mapping_index_variable:
        try:
            mapping_index = globals()[mapping_index_variable.upper()]
        except:
            pass

    total = 0
    correct = 0
    ambiguous = 0
    error = 0
    skipped = 0
    wrong_data = []
    for r in output_data:
        if r['index'] in mapping_index:
            skipped +=1
            continue
        if r['majority_ans'] == r['answer']:
            correct += 1
        elif r['majority_ans'] == 'Ambiguous':
            ambiguous +=1
        elif r['majority_ans'] is None:
            error += 1
            wrong_data.append(r)
        else:
            wrong_data.append(r)
        total += 1

    print(f'Accuracy: {correct/total}, Total: {total}, Correct: {correct}, Error: {error}, Skipped: {skipped}, Ambiguous: {ambiguous}')
    if wrong:
        jsonlines_dump(get_save_path(input_path),wrong_data)