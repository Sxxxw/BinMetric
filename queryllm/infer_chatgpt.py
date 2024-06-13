'''
@desc: query chatgpt
@requirements: termcolor, openai, tiktoken
@usage: python3 thisfile.py
'''
import os
import re
import sys
import json
import time
import random
from tqdm import tqdm
from openai import OpenAI
from termcolor import colored
from utils import read_json_file, read_jsonline_file, write_json_file, write_jsonline_file, generate_prompt
sys.path.append(os.path.abspath("../"))
from evaluator.config import TASKTYPE_POSTPROCESS_DICT

api_key_list = [
                ('sk-xxxx-xxxxxxxxxx', 'tier1')
                ]             
MODEL = "gpt-3.5-turbo-16k-0613"
MAX_TOKEN_LENGTH = 16000

json_file_path = "../problem_data.json"
save_file_path = "./chatgpt_prediction.jsonl"

random.seed(233)
TYPES_OF_LIMITS_PER_MINNUTE = {
    "free": 60/3,
    "tier1": 60/500,
    "tier2": 60/5000,
    "tier3": 60/5000,
    "tier4": 60/10000,
    "tier5": 60/10000,
}

class KeyPool():
    '''
    code example:
    key_list = [
        ('sk-xxxxxxxxxx', 'free'),
    ]
    key_pool = KeyPool(key_list)
    while NEED_QUERY():
        key = key_pool.get_key():
        content = do_query()
        status = key_pool.judge_status(content)
        key_pool.feedback(key, status)
    '''
    def __init__(self, key_list) -> None:
        random.shuffle(key_list)
        self.key_list = []
        for item in key_list:
            _key,_type = item
            self.key_list.append({
                "key": _key,
                "type": _type,
                "ok_time": time.time(),
            })
        self.cur_idx = 0
        print(colored('[+] load keys:','blue'))
        print(json.dumps(self.key_list, indent=4))

    def get_key(self):
        while True:
            item = self.key_list[self.cur_idx]
            self.cur_idx = (self.cur_idx + 1) % len(self.key_list)
            if item['ok_time'] <= time.time():
                return item['key']
    
    def feedback(self, key, status):
        for item in self.key_list:
            if item['key'] == key:
                if status == 'good':
                    _type = item['type']
                    item['ok_time'] = time.time() + TYPES_OF_LIMITS_PER_MINNUTE[_type]
                elif status == 'PRM_limit':
                    _type = item['type']
                    item['ok_time'] = time.time() + TYPES_OF_LIMITS_PER_MINNUTE[_type]               
                elif status == 'RPD_limit':
                    _type = item['type']
                    item['ok_time'] = time.time() + 3600*24
                elif status == 'exceeded_quota':
                    _type = item['type']
                    item['ok_time'] = time.time() + 1e9
                else:
                    raise NotImplementedError
    
    def judge_status(self, content):
        if 'Error code: 429' in content:
            if 'RPM' in content:
                return "PRM_limit"
            elif 'RPD' in content:
                return "RPD_limit"
            elif 'You exceeded your current quota' in content:
                return "exceeded_quota"
            else: 
                raise NotImplementedError
        else:
            return "good"

def checkpoint(data, save_file_path):
    if not os.path.exists(save_file_path):
        return data
    if save_file_path.endswith('.json'):
        done_data = read_json_file(save_file_path)
    elif save_file_path.endswith('.jsonl'):
        done_data = read_jsonline_file(save_file_path)
    else:
        raise NotImplementedError

    done_fids = {d['task_id']:d for d in done_data}
    new_data = []
    cnt = 0
    for item in data:
        if item['task_id'] in done_fids:
            new_data.append(done_fids[item['task_id']])
            cnt+=1
        else:
            new_data.append(item)
    print('[+] checkpoint:', cnt, 'data has been done.')
    return new_data

def call_chatgpt(prompt, api_key):
    try:
        client = OpenAI(
            api_key=api_key,
        )
        completion = client.chat.completions.create(
            messages = [
                {"role": "user", "content": prompt}
                ],
            model = MODEL,
        )
    except Exception as e:
        return str(e)
    return completion.choices[0].message.content

def parse_code_in_block(prompt, output):
    pattern = r'```[a-zA-Z+]*\n(.+?)\n\s*```'
    match = re.search(pattern, output, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return ""

def save_all_generated(prompt, output):
    return output

def parse_model_output(sample, prompt, output):
    func_str = TASKTYPE_POSTPROCESS_DICT[sample['task_type']]
    func = getattr(sys.modules[__name__], func_str)
    return func(prompt, output)

def main(sleep_time=20):
    data = read_json_file(json_file_path)
    data = checkpoint(data, save_file_path)
    
    key_pool = KeyPool(api_key_list)

    for item in tqdm(data):
        if 'completion' in item:
            continue

        while True:
            api_key = key_pool.get_key()

            input_text = generate_prompt(item)
            response = call_chatgpt(input_text, api_key)
            print(colored("[-] response:\n",'blue'),colored(response,'green'))

            status = key_pool.judge_status(response)
            key_pool.feedback(api_key, status)
            if status == 'good':
                break
        item['raw_output'] = response
        item['completion'] = parse_model_output(item, input_text, response)
        write_jsonline_file(save_file_path,item)

if __name__ == '__main__':
    main()