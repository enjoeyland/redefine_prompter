import argparse
from tool import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', type=str, required=True)
    args = parser.parse_args()

    input_path = args.input_path

    output_data = jsonlines_load(input_path)

    total = 0
    correct = 0
    error = 0
    for r in output_data:
        if r['majority_ans'] == r['answer']:
            correct += 1
        elif r['majority_ans'] is None:
            error += 1

        total += 1

    print(f'Accuracy: {correct/total}, Total: {total}, Correct: {correct}, Error: {error}')
