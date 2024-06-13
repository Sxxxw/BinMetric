import re
import os
import sys
import time
import json
import jsonlines
sys.path.append(os.path.abspath("../"))
from evaluator.config import TASKTYPE_POSTPROCESS_DICT


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def read_jsonline_file(file_path):
    with jsonlines.open(file_path) as reader:
        data = [d for d in reader]
    return data

def _write_file(dataset, path):
    if path.endswith('.jsonl'):
        with jsonlines.open(path, 'w') as writer:
            for data in dataset:
                writer.write(data)
    elif path.endswith('.json'):
        with open(path, 'w') as writer:
            json.dump(dataset, writer, indent=4)
    else:
        raise NotImplementedError("[!] Unsupported file format. Please use .json or .jsonl file.")

def write_json_file(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def write_jsonline_file(file_path, data):
    with jsonlines.open(file_path, 'a') as writer:
        writer.write(data)

def save_solution(dataset: list, path: str):
    return _write_file(dataset, path)

def find_whole_word(word, text):
    pattern = r'\b{}\b'.format(re.escape(word))
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def checkpoint(save_file_path):
    if save_file_path.endswith('.json'):
        done_data = read_json_file(save_file_path)
    elif save_file_path.endswith('.jsonl'):
        done_data = read_jsonline_file(save_file_path)
    else:
        raise NotImplementedError
    
    finish_num = 0
    for item in done_data:
        if "completion" in item:
            finish_num += 1
    print(f'[+] checkpoint: {finish_num}/{len(done_data)} data has been done.')
    time.sleep(3)
    return done_data, finish_num

def parse_code_in_block(prompt, output):
    if "### Response:" in output:
        output = output.split("### Response:")[1].strip()
    else:
        raise Exception("Generation Error: output does not start with prompt.\n"+output)
    pattern = r'```[a-zA-Z+]*\n\s*(.+?)\n\s*```'
    match = re.search(pattern, output, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return ""

def save_all_generated(prompt, output):
    if "### Response:" in output:
        output = output.split("### Response:")[1].strip()
    else:
        raise Exception("Generation Error: output does not start with prompt.\n"+output)
    return output

def parse_model_output(sample, prompt, output):
    func_str = TASKTYPE_POSTPROCESS_DICT[sample['task_type']]
    func = getattr(sys.modules[__name__], func_str)
    return func(prompt, output)

PROMPT_ONESHOT_CSR="""
Here is an example that asks to output the call point at 'call sub_116C' in the form of C source code:

Example input assembly code: 
```
endbr64\npush    rbp\nmov     rbp, rsp\nsub     rsp, 30h\nmov     [rbp+var_18], rdi\nmov     [rbp+var_20], rsi\nmov     [rbp+var_28], rdx\nmov     [rbp+var_4], 0\nmov     rax, [rbp+var_18]\nmov     rdi, rax\ncall    _curl_mime_init\nmov     rdx, rax\nmov     rax, [rbp+var_28]\nmov     [rax], rdx\nmov     rax, [rbp+var_28]\nmov     rax, [rax]\ntest    rax, rax\njnz     short loc_119C0\nmov     [rbp+var_4], 1Bh\njmp     short loc_119E1\nmov     rax, [rbp+var_28]\nmov     rdx, [rax]\nmov     rax, [rbp+var_20]\nmov     rcx, [rax+48h]\nmov     rax, [rbp+var_18]\nmov     rsi, rcx\nmov     rdi, rax\ncall    sub_116C7\nmov     [rbp+var_4], eax\ncmp     [rbp+var_4], 0\njz      short loc_11A01\nmov     rax, [rbp+var_28]\nmov     rax, [rax]\nmov     rdi, rax\ncall    _curl_mime_free\nmov     rax, [rbp+var_28]\nmov     qword ptr [rax], 0\nmov     eax, [rbp+var_4]\nleave\nretn
``` 

Example output: 
```
tool2curlparts(curl, m->subparts, *mime)
```
"""

PROMPT_ONESHOT_DEC = """
Here is one example: 

Example input assembly code: 
```
endbr64\npush    rbp\nmov     rbp, rsp\npush    rbx\nsub     rsp, 68h\nmov     [rbp+var_58], rdi\nmov     [rbp+var_5C], esi\nmov     [rbp+var_68], rdx\nmov     [rbp+var_70], rcx\ncmp     [rbp+var_5C], 0\njg      short loc_8A266\nlea     rsi, aWrongArgs  \"wrong args\"\nlea     rdi, aVips816_32  \"vips8.16\"\ncall    _g_dgettext\nmov     rdx, rax\nlea     rsi, aS_22  \"%s\"\nlea     rdi, aImMeanStdIntBu  \"im_mean_std_int_buffer\"\nmov     eax, 0\ncall    _vips_error\nmov     eax, 0FFFFFFFFh\njmp     loc_8A334\npxor    xmm0, xmm0\nmovsd   [rbp+var_30], xmm0\npxor    xmm0, xmm0\nmovsd   [rbp+var_28], xmm0\nmov     [rbp+var_44], 0\nmov     [rbp+var_40], 0\nmov     rax, [rbp+var_58]\nmov     [rbp+var_38], rax\nmov     ebx, 0\njmp     short loc_8A2B9\nmov     rax, [rbp+var_38]\nlea     rdx, [rax+4]\nmov     [rbp+var_38], rdx\nmov     eax, [rax]\nmov     [rbp+var_3C], eax\nmov     eax, [rbp+var_3C]\nadd     [rbp+var_44], eax\nmov     eax, [rbp+var_3C]\nimul    eax, [rbp+var_3C]\nadd     [rbp+var_40], eax\nadd     ebx, 1\ncmp     ebx, [rbp+var_5C]\njl      short loc_8A295\nmov     eax, [rbp+var_44]\nimul    eax, [rbp+var_44]\ncvtsi2sd xmm0, eax\ncvtsi2sd xmm1, [rbp+var_5C]\ndivsd   xmm0, xmm1\nmovsd   [rbp+var_20], xmm0\ncvtsi2sd xmm0, [rbp+var_44]\ncvtsi2sd xmm1, [rbp+var_5C]\ndivsd   xmm0, xmm1\nmovsd   [rbp+var_30], xmm0\ncvtsi2sd xmm0, [rbp+var_40]\nsubsd   xmm0, [rbp+var_20]\ncvtsi2sd xmm1, [rbp+var_5C]\ndivsd   xmm0, xmm1\nmovsd   [rbp+x], xmm0\nmovsd   xmm0, [rbp+x]  x\ncall    _sqrt\nmovq    rax, xmm0\nmov     [rbp+var_28], rax\nmov     rax, [rbp+var_68]\nmovsd   xmm0, [rbp+var_30]\nmovsd   qword ptr [rax], xmm0\nmov     rax, [rbp+var_70]\nmovsd   xmm0, [rbp+var_28]\nmovsd   qword ptr [rax], xmm0\nmov     eax, 0\nadd     rsp, 68h\npop     rbx\npop     rbp\nretn
``` 

Example output source code: 
```C
int\nim__mean_std_int_buffer(int *buffer, int size,\n\tdouble *pmean, double *pstd)\n{\n\tdouble mean, std;\n\tregister int i;\n\tint sumf;\n\tint temp;\n\tint *pbuffer;\n\tint sumf2;\n\tdouble correction; /* calulates the correction term for the variance */\n\tdouble variance;   /* = (sumf2 - correction)/n */\n\n\tif (size <= 0) {\n\t\tim_error(\"im_mean_std_int_buffer\", \"%s\", _(\"wrong args\"));\n\t\treturn -1;\n\t}\n\n\tmean = 0.0;\n\tstd = 0.0;\n\tsumf = 0;\n\tsumf2 = 0;\n\tpbuffer = buffer;\n\tfor (i = 0; i < size; i++) {\n\t\ttemp = *pbuffer++;\n\t\tsumf += temp;\n\t\tsumf2 += (temp * temp);\n\t}\n\n\tcorrection = ((double) (sumf * sumf)) / ((double) size);\n\tmean = ((double) sumf) / ((double) size);\n\tvariance = (sumf2 - correction) / ((double) size);\n\tstd = sqrt(variance);\n\t*pmean = mean;\n\t*pstd = std;\n\n\treturn 0;\n} \n
```
"""

PROMPT_ONESHOT_SR = """
Here is one example: 

Example input decompiled C function:  
```C
__int64 sub_95590(__int64 a1, _QWORD *a2, _QWORD *a3, __int64 a4, __int64 a5, __int64 a6, ...)\n{\n  // [COLLAPSED LOCAL DECLARATIONS. PRESS KEYPAD CTRL-\"+\" TO EXPAND]\n\n  va_start(va, a6);\n  v12 = a4;\n  v13 = a5;\n  v14 = a6;\n  v11 = __readfsqword(0x28u);\n  v9 = 0LL;\n  va[0].gp_offset = 24;\n  v8 = vips_call_split(\"dzsave_buffer\", va, a1, &v9);\n  if ( !v8 && v9 )\n  {\n    if ( a2 )\n    {\n      *a2 = *v9;\n      v9[4] = 0LL;\n    }\n    if ( a3 )\n      *a3 = v9[1];\n    j_vips_area_unref(v9);\n  }\n  return v8;\n}\n"
``` 

Example function signature: 
```
int vips_dzsave_buffer(VipsImage * in, void ** buf, size_t * len)
```
"""

PROMPT_ONESHOT_BCS = """
Here is one example: 

Example input decompiled C function: 
```C
void __fastcall sub_95590(const char *a1, __int64 a2)\n{\n  int *v2; // rax\n  char *v3; // rax\n\n  if ( !a2 )\n    __assert_fail(\"dictFileStat != NULL\", \"fileio.c\", 0x2ADu, \"FIO_getDictFileStat\");\n  if ( a1 )\n  {\n    if ( !(unsigned int)sub_1AEC79(a1, a2) )\n    {\n      if ( dword_1E70F8 > 0 )\n        fwrite(\"zstd: \", 1uLL, 6uLL, stderr);\n      if ( dword_1E70F8 > 4 )\n        fprintf(stderr, \"Error defined at %s, line %i : \\n\", \"fileio.c\", 689LL);\n      if ( dword_1E70F8 > 0 )\n        fprintf(stderr, \"error %i : \", 31LL);\n      if ( dword_1E70F8 > 0 )\n      {\n        v2 = __errno_location();\n        v3 = strerror(*v2);\n        fprintf(stderr, \"Stat failed on dictionary file %s: %s\", a1, v3);\n      }\n      if ( dword_1E70F8 > 0 )\n        fwrite(\" \\n\", 1uLL, 2uLL, stderr);\n      exit(31);\n    }\n    if ( !(unsigned int)sub_1AEDE8(a2) )\n    {\n      if ( dword_1E70F8 > 0 )\n        fwrite(\"zstd: \", 1uLL, 6uLL, stderr);\n      if ( dword_1E70F8 > 4 )\n        fprintf(stderr, \"Error defined at %s, line %i : \\n\", \"fileio.c\", 693LL);\n      if ( dword_1E70F8 > 0 )\n        fprintf(stderr, \"error %i : \", 32LL);\n      if ( dword_1E70F8 > 0 )\n        fprintf(stderr, \"Dictionary %s must be a regular file.\", a1);\n      if ( dword_1E70F8 > 0 )\n        fwrite(\" \\n\", 1uLL, 2uLL, stderr);\n      exit(32);\n    }\n  }\n}
``` 

Example output short comment: 
This function, `FIO_getDictFileStat`, takes in a file name and a `stat_t` structure. It first checks if the `dictFileStat` structure is not NULL, and if the `fileName` is NULL, it directly returns. \n\nNext, it uses the `UTIL_stat` function to get the statistics of the file specified by `fileName` and stores it in the `dictFileStat` structure. If the `UTIL_stat` function fails, it throws an exception with error code 31 and a specific error message.\n\nThen, it checks if the file specified by `fileName` is a regular file using the `UTIL_isRegularFileStat` function. If it is not a regular file, it throws an exception with error code 32 and a specific error message.
"""

PROMPT_ONESHOT_AIG = """
The following is an Intel syntax style assembly code that adds two input numbers and prints the result to the console:

```
.intel_syntax noprefix\n.text\n.section\t.rodata\n.LC0:\n.string\t"%d %d"\n.LC1:\n.string\t"%d\n"\n.text\n.globl\tmain\n.type\tmain, @function\nmain:\n.LFB0:\n.cfi_startproc\nendbr64\npush\trbp\n.cfi_def_cfa_offset 16\n.cfi_offset 6, -16\nmov\trbp, rsp\n.cfi_def_cfa_register 6\nsub\trsp, 16\nmov\trax, QWORD PTR fs:40\nmov\tQWORD PTR -8[rbp], rax\nxor\teax, eax\nlea\trdx, -12[rbp]\nlea\trax, -16[rbp]\nmov\trsi, rax\nlea\trdi, .LC0[rip]\nmov\teax, 0\ncall\t__isoc99_scanf@PLT\nmov\tedx, DWORD PTR -16[rbp]\nmov\teax, DWORD PTR -12[rbp]\nadd\teax, edx\nmov\tesi, eax\nlea\trdi, .LC1[rip]\nmov\teax, 0\ncall\tprintf@PLT\nmov\teax, 0\nmov\trcx, QWORD PTR -8[rbp]\nxor\trcx, QWORD PTR fs:40\nje\t.L3\ncall\t__stack_chk_fail@PLT\n.L3:\nleave\n.cfi_def_cfa 7, 8\nret\n.cfi_endproc\n
```

Please refer to the above code."""

PROMPT_ONESHOT_AC = """
Here is one example: 

Example input decompiled C function:  
```C
void __fastcall sub_1230(int *a1, int a2)\n{\n  int v2; // r9d\n  int *v3; // rax\n  char v4; // r8\n  __int64 v5; // rsi\n  int v6; // edx\n  int v7; // ecx\n\n  if ( a2 != 1 )\n  {\n    do\n    {\n      v2 = a2 - 1;\n      if ( a2 - 1 <= 0 )\n        break;\n      v3 = a1;\n      v4 = 0;\n      v5 = (__int64)&a1[a2 - 2 + 1];\n      do\n      {\n        v6 = *v3;\n        v7 = v3[1];\n        if ( *v3 > v7 )\n        {\n          *v3 = v7;\n          v4 = 1;\n          v3[1] = v6;\n        }\n        ++v3;\n      }\n      while ( (int *)v5 != v3 );\n      if ( !v4 )\n        break;\n      a2 = v2;\n    }\n    while ( v2 != 1 );\n  }\n}\n  \n  void __fastcall swap(int *first, int *second)\n{\n  int v2; // eax\n\n  v2 = *first;\n  *first = *second;\n  *second = v2;\n}\n
``` 

Example output:
``` 
Sorting
```
"""

template_dict = {
    "CSR": PROMPT_ONESHOT_CSR,
    "AC": PROMPT_ONESHOT_AC,
    "AIG": PROMPT_ONESHOT_AIG,
    "DEC": PROMPT_ONESHOT_DEC,
    "SR": PROMPT_ONESHOT_SR,
    "BCS": PROMPT_ONESHOT_BCS,
} 

def generate_prompt(sample, template="zero"):  # zero / few
    prompt_template = sample['instruction']
    if template=="few":
        return prompt_template.format(input=sample['input'], example=template_dict[sample["task_type"]])
    else:
        return prompt_template.format(input=sample['input'], example="")

