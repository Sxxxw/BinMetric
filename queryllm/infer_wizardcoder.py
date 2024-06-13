import os
import sys
import time
import fire
import torch
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer, GenerationConfig
from utils import chunks, generate_prompt, checkpoint, read_json_file, save_solution, parse_model_output

torch.cuda.empty_cache() 
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def sort_by_pcode_length(dataset):
    return sorted(dataset, key=lambda x: len(x["pcode"]))

def evaluate(
        chunk,
        tokenizer,
        model,
        max_length=8192,
        max_new_tokens=2048
):
    prompt_text = [generate_prompt(sample) for sample in chunk]
    
    inputs = tokenizer(prompt_text, return_tensors="pt", max_length=max_length, truncation=True, padding=True).to(device)

    generation_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=True,
        num_beams=1,
        top_k=1,
        top_p=1,
        temperature=0.1,
        eos_token_id=tokenizer.eos_token_id,
        pad_token_id=tokenizer.pad_token_id
    )
    start_time = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            generation_config=generation_config,
        )
    overhead = time.time() - start_time
    decoded_outputs = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    outputs = [parse_model_output(sample, prompt, output) for sample, prompt, output in zip(chunk, prompt_text, decoded_outputs)]
    return decoded_outputs, outputs, overhead

def main(
    load_8bit: bool = False,
    batch_size: int = 1, 
    base_model_path: str = "/archive/LLMs/WizardCoder-15B-V1.0",  
    input_data_path: str = "../problem_data.json",
):
    assert base_model_path, (
        "Please specify a --base_model, e.g. --base_model='bigcode/starcoder'"
    )
    
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    tokenizer.padding_side = "left"

    model = AutoModelForCausalLM.from_pretrained(
        base_model_path, 
        device_map="auto", 
        load_in_8bit=load_8bit,
        torch_dtype=torch.float16, 
    )

    if not load_8bit:
        model.bfloat16()

    model.eval()
    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)

    model_name = base_model_path.split('/')[-1]
    output_path = model_name + "_prediction.json"
    if os.path.exists(output_path):
        dataset, breakpoint = checkpoint(output_path)
    else:
        dataset = read_json_file(input_data_path)  
        breakpoint = 0
    print("Total Num:", len(dataset), "Remain Num:", len(dataset[breakpoint:]))

    for chunk in tqdm(list(chunks(dataset[breakpoint:], batch_size))):
        raw_outputs, outputs, overhead = evaluate(chunk, tokenizer, model)
        for sample, raw_output, output in zip(chunk, raw_outputs, outputs):
            sample['raw_output'] = raw_output
            sample['completion'] = output
            sample['overhead'] = overhead

        save_solution(dataset, output_path)

if __name__ == "__main__":
    fire.Fire(main)
