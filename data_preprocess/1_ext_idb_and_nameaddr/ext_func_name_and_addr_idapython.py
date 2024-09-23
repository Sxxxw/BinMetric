import os
import sark
import json
import ida_pro
import ida_nalt
import ida_auto
ida_auto.auto_wait()

inputFileName = ida_nalt.get_root_filename()
NAME_ADDR_JSON_SUFFIX = os.environ["NAME_ADDR_JSON_SUFFIX"] if "NAME_ADDR_JSON_SUFFIX" in os.environ else ".name_and_addr.json"

text_segment = sark.Segment(name='.text')
if len(list(text_segment.functions)) == 0:
    ida_pro.qexit(0)

methods = dict()
for func in text_segment.functions:
    methods[func.demangled] = [func.start_ea, func.end_ea]

with open(inputFileName+NAME_ADDR_JSON_SUFFIX, 'w', encoding="utf-8") as f:
    json.dump(methods, f, indent=4)

ida_pro.qexit(0)
