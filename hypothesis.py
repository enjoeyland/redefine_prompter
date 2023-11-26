from tool import *
from scipy.stats import ttest_ind
if __name__ == '__main__':
    output_data = jsonlines_load("output\chatgpt\mapping.jsonl")

    wrong_original = []
    correct = []
    correct_rate = []
    wrong = []
    wrong_rate = []
    for r in output_data:
        if not r['original']:
            wrong_original.append(r['index'])
        elif r['majority_ans'] == r['answer']:
            correct.append(r['index'])
            correct_rate.append(r['avg_rate'])
        elif r['majority_ans'] != 'Ambiguous':
            wrong.append(r['index'])
            wrong_rate.append(r['avg_rate'])

    print(f'correct={len(correct)}, correct_rate={sum(correct_rate)/len(correct_rate)}, wrong={len(wrong)}, wrong_rate={sum(wrong_rate)/len(wrong_rate)}')
    print(ttest_ind(correct_rate, wrong_rate, equal_var=False))