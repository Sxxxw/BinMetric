'''
extract function info from ida pro database, and save to json file
function info include: function name, md5 hash, asm code, cfg, pseudo code
more see idapython file

DIR_STRIPPED_IDB: idb file, unstrip binary name_addr_json

[!] skip mips_64, hexray decomipler not support
'''
import os
import sys
import time
import shutil
import logging
import subprocess
from tqdm import tqdm
from glob import glob
from multiprocessing import Pool, Queue, Process, cpu_count
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s| %(levelname)s| %(message)s')

DIR_STRIPPED_IDB = "./github-proj/binary-strip-idb"
IDA_PYTHON_SCRIPT = "./idascript/2_ext_func/ext_func_multipleinfo_idapython.py"
OVERWRITE_RESULTS_JSON = False

IDA_IDB_DICT = {64:('ida64','.i64'), 32:("ida",".idb")}
threads = 8
IDA_TIMEOUT=60*60*12 # second
IDB_SUFFIX = (".i64",".idb")
NAME_ADDR_JSON_SUFFIX = ".name_and_addr.json"
FUNC_INFO_JSON_SUFFIX = ".multi.json"
FILTER_CPP_FUNC = "True"
FILTER_EXPORT_FUNC = "False"
os.environ["NAME_ADDR_JSON_SUFFIX"] = NAME_ADDR_JSON_SUFFIX
os.environ["FUNC_INFO_JSON_SUFFIX"] = FUNC_INFO_JSON_SUFFIX
os.environ["FILTER_CPP_FUNC"] = FILTER_CPP_FUNC
os.environ["FILTER_EXPORT_FUNC"] = FILTER_EXPORT_FUNC


def disassemble_one(file_queue, failed, thread_id):
    while not file_queue.empty():
        file = file_queue.get()
        remain_count = file_queue.qsize()
        try:
            bit = 64 if file.endswith(".i64") else 32
            IDA, IDB_SUFFIX = IDA_IDB_DICT[bit]
            binary_file = file[:-4]
            if not OVERWRITE_RESULTS_JSON and os.path.exists(binary_file+FUNC_INFO_JSON_SUFFIX):
                print(f'[t{thread_id}] remain {remain_count} file {file} already done')
                continue
            print(f'[t{thread_id}] remain {remain_count} disassembling file {file}')
            cmd = f"{IDA} -A -S{IDA_PYTHON_SCRIPT} {file}"
            subprocess.check_output(cmd, timeout=IDA_TIMEOUT)
            if not os.path.exists(binary_file+FUNC_INFO_JSON_SUFFIX):
                raise Exception(f"{binary_file} result file not found")
        except Exception as e:
            print("[!]", e)
            failed.put(file+"\n"+str(e))

def multi_thread_main():
    # get all file
    idbs = []
    for root, dirs, files in os.walk(DIR_STRIPPED_IDB):
        for name in files:
            if name.endswith(IDB_SUFFIX):
                if "mips_64" in name: # skip mips_64, hexray decomipler not support
                    continue
                idbs.append(os.path.join(root, name))
    print(f"[-] found {len(idbs)} idb files")
    # run 
    queue = Queue()
    failed = Queue()
    for f in idbs:
        queue.put(f)
    processes = [Process(target=disassemble_one, args=(queue,failed,i+1,)) for i in range(threads)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    # log to file
    print(f"[!] failed files count {failed.qsize()}, save to failed.txt")
    with open("failed.txt","a+",encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+" logging \n")
        f.write(f"[-] DIR_STRIPPED_IDB: {DIR_STRIPPED_IDB}\n")
        f.write(f"[-] failed files count {failed.qsize()}\n")
        while not failed.empty():
            f.write(failed.get()+"\n")


import signal
def signal_handler(sig, frame):
    print('You pressed Ctrl+C! Main process will exit after all subprocesses done!')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    start_time = time.time()
    multi_thread_main()
    end_time = time.time()
    print('[+] Time cost:', int(end_time-start_time))
