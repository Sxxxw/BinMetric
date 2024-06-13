import os
import gzip
import json
from typing import Iterable, Dict

from .config import PROMPT_TEMPLATE

current_path = os.path.dirname(os.path.abspath(__file__))
EVAL_DATA_PATH = os.path.join(current_path, "eval_data.json")
'''eval_data.json
[
	{
		"id": 0,
		"task_type": "TNAME1",
		"input": "input text",
		"output": "output text",
		"default_instruction": "specific one for each task",
        "candidate_instruction": ["candidate_instruction 111"]
	},
	...
]
'''


def read_problems(evalset_file: str = EVAL_DATA_PATH) -> Dict[str, Dict]:
    return {task["task_id"]: task for task in read_jsonl(evalset_file)}


def read_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary
    """
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, 'rt') as fp:
                for line in fp:
                    if any(not x.isspace() for x in line):
                        yield json.loads(line)
    else:
        with open(filename, "r") as fp:
            dataset = json.load(fp)
        for data in dataset:
            yield data


def write_jsonl(filename: str, data: Iterable[Dict], append: bool = False):
    """
    Writes an iterable of dictionaries to jsonl
    """
    if append:
        mode = 'ab'
    else:
        mode = 'wb'
    filename = os.path.expanduser(filename)
    if filename.endswith(".gz"):
        with open(filename, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode='wb') as gzfp:
                for x in data:
                    gzfp.write((json.dumps(x) + "\n").encode('utf-8'))
    else:
        with open(filename, mode) as fp:
            for x in data:
                fp.write((json.dumps(x) + "\n").encode('utf-8'))


def generate_one_prompt(problem):
    input = problem['input']
    default_instruction = problem['default_instruction']
    prompt = PROMPT_TEMPLATE['DEFAULT'].format(
        input=input,
        default_instruction=default_instruction
    )
    return prompt


if __name__ == '__main__':
    problems = read_problems()
    for task_id, problem in problems.items():
        print(task_id, problem)
        print(generate_one_prompt(problem))
        break