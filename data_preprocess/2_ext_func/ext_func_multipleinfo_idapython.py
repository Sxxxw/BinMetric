import os
import sark
import json
import idc
import ida_nalt
import ida_auto
import ida_pro
import hashlib
from ida_hexrays import decompile, DecompilationFailure
ida_auto.auto_wait()
NAME_ADDR_JSON_SUFFIX = os.environ["NAME_ADDR_JSON_SUFFIX"]
FUNC_INFO_JSON_SUFFIX = os.environ["FUNC_INFO_JSON_SUFFIX"]
FILTER_CPP_FUNC = eval(os.environ["FILTER_CPP_FUNC"])
FILTER_EXPORT_FUNC = eval(os.environ["FILTER_EXPORT_FUNC"])
# default value for debug
# NAME_ADDR_JSON_SUFFIX = ".name_and_addr.json"
# FUNC_INFO_JSON_SUFFIX = ".multi.json"
# FILTER_CPP_FUNC = True
# FILTER_EXPORT_FUNC = False

def is_cplusplus_func(func_name):
    return '(' in func_name and ')' in func_name

inputFileName = ida_nalt.get_root_filename()

if idc.get_idb_path().endswith('.i64'):
    cpu_width = 64
else:
    cpu_width = 32

# if inputFileName.endswith(".stripped"):
#     name_and_addr = inputFileName[:-len(".stripped")]+NAME_ADDR_JSON_SUFFIX
# elif inputFileName.endswith(".strip"):
#     name_and_addr = inputFileName[:-len(".strip")]+NAME_ADDR_JSON_SUFFIX
# else:
#     name_and_addr = inputFileName+NAME_ADDR_JSON_SUFFIX
name_and_addr = inputFileName+NAME_ADDR_JSON_SUFFIX

if not os.path.exists(name_and_addr):
    ida_pro.qexit(0)

with open(name_and_addr,"r") as f:
    method_dict = json.load(f)
method_dict = {f"{v[0]}-{v[1]}":k for k, v in method_dict.items()}

text_segment = sark.Segment(name='.text')
funcs = list(text_segment.functions)
if len(funcs) == 0:
    ida_pro.qexit(0)

# filter functions with unknown names, "exports functions" have its name
if FILTER_EXPORT_FUNC:
    funcs = list(filter(lambda x: not x.has_name, funcs))

print("[+] analysis start")
methods = []
for func in funcs:
    addr = f"{func.start_ea}-{func.end_ea}"
    if addr not in method_dict:
        continue
    
    func_name = method_dict[addr]
    # if FILTER_CPP_FUNC and is_cplusplus_func(sark.demangle(func_name)):
        # name, symbolname, demangle name
        # continue
    
    # get md5 hash
    bytes = idc.get_bytes(func.start_ea, func.end_ea-func.start_ea)
    md5 = hashlib.md5(bytes).hexdigest()
    # get asm code
    func_instructions = []
    for line in func.lines:
        instruction = line.disasm
        #instruction = instruction.split(";")[0]
        func_instructions.append([line.ea, instruction])
    # get cfg
    basic_blocks = []
    basic_blocks_dict = dict()
    for idx, bb in enumerate(sark.FlowChart(func.func_t)):
        basic_blocks.append([idx, bb.start_ea, bb.end_ea]) # [start_ea, end_ea) for asm line
        basic_blocks_dict[f"{bb.start_ea}-{bb.end_ea}"] = idx
    edges = []
    for bb in sark.FlowChart(func.func_t):
        bb_id = basic_blocks_dict[f"{bb.start_ea}-{bb.end_ea}"]
        for next_bb in bb.next:
            next_bb_id = basic_blocks_dict[f"{next_bb.start_ea}-{next_bb.end_ea}"]
            edges.append([bb_id, next_bb_id])
    # get pseudo code
    try:
        pseudo_code = str(decompile(func.ea))
    except DecompilationFailure:
        continue

    methods.append({
        "start": func.start_ea,
        "end": func.end_ea,
        "name": func_name,
        "md5": md5,
        "asm": func_instructions,
        "blocks": basic_blocks,
        "cfg": edges,
        "pcode": pseudo_code,
        })

print("[+] analysis done")
with open(inputFileName+FUNC_INFO_JSON_SUFFIX, 'w', encoding="utf-8") as f:
    json.dump(methods, f, indent=4)

ida_pro.qexit(0)
