import os
import sys
import json
import time
import torch
import jsonlines
from tqdm import tqdm
from termcolor import colored
from transformers import AutoTokenizer, AutoModelForCausalLM, GenerationConfig


def load_model_and_tokenizer(model_path):
    model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map="auto")
    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    tokenizer.pad_token_id = 0
    tokenizer.padding_side = "left"
    return model, tokenizer

def generate_prompt(input):
    return f"The following is a comment for a C/C++ function. You need to pick out the words that are important to the semantic description and list them, separated by commas (,):\n{input}"

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def find_keywords(model, tokenizer, inputs, batch_size=1):
    generation_config = GenerationConfig(
        max_length=512,
        max_new_tokens=64,
        num_beams=1,
        no_repeat_ngram_size=4,
        num_return_sequences=1,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.8,
        use_cache=True,
        pad_token_id=tokenizer.pad_token_id,
    )
    outputs = []
    prompts = [generate_prompt(inp) for inp in inputs]
    for batch_prompts in tqdm(list(chunks(prompts, batch_size))):
        encodings = tokenizer(batch_prompts, return_tensors="pt", padding=True).to('cuda')
        generation_outputs = model.generate(
            **encodings,
            generation_config=generation_config,
        )
        batch_outputs = tokenizer.batch_decode(generation_outputs, skip_special_tokens=True)
        for i in range(len(batch_outputs)):
            batch_outputs[i] = batch_outputs[i].replace(batch_prompts[i],'')
            print(batch_outputs[i])
        outputs.extend(batch_outputs)
    return prompts,outputs

if __name__ == "__main__":
    model_path = "/archive/CodeLlama-34b-Instruct-hf/" # at least use codellama-34b-insturct, I have not try llama2-34b-instruct
    model, tokenizer = load_model_and_tokenizer(model_path)
    import jsonlines
    jsonl_path = "../scode_gpt-3.5-turbo-16k.jsonl"
    with jsonlines.open(jsonl_path, 'r') as reader:
        input_list = list(reader)
        input_list = [d['chatgpt_raw'] for d in input_list]
    input_list = input_list[3200:3202]
    print(len(input_list))
    prompts,outputs = find_keywords(model, tokenizer, input_list)
    for i,j in zip(prompts,outputs):
        print('='*50)
        print(colored(i,'red'))
        print(colored(j,'green'))
        print('='*50)