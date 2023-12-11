from tool import *
from scipy.stats import ttest_ind
if __name__ == '__main__':
    output_data = jsonlines_load("output\chatgpt\mapping.jsonl")

    wrong_original = []
    correct = []
    correct_rank = []
    wrong = []
    wrong_rank = []
    error = []
    error_rank = []
    for r in output_data:
        if not r['original']:
            wrong_original.append(r['index'])
        elif r['majority_ans'] == r['answer']:
            correct.append(r['index'])
            correct_rank.append(r['avg_rank'])
        elif r['majority_ans']:
            wrong.append(r['index'])
            wrong_rank.append(r['avg_rank'])
        else:
            error.append(r['index'])
            error_rank.append(r['avg_rank'])
    print(f'correct={len(correct)}, correct_rank={sum(correct_rank)/len(correct_rank)}')
    print(f'wrong={len(wrong)}, wrong_rank={sum(wrong_rank)/len(wrong_rank)}')
    if error:
        print(f'error={len(error)}, error_rank={sum(error_rank)/len(error_rank)}')
    else:
        print(f'error={len(error)}')
    
    print()
    print("correct vs wrong")
    print(ttest_ind(correct_rank, wrong_rank, equal_var=False))
    if len(error) > 4:
        print("correct vs error")
        print(ttest_ind(correct_rank, error_rank, equal_var=False))
        print("wrong vs error")
        print(ttest_ind(wrong_rank, error_rank, equal_var=False))
