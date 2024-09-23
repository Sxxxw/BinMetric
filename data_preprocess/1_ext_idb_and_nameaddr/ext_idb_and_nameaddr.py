'''
generate idb and func_name_addr.json for files in DIR_UNSTRIPPED_BINARY and DIR_STRIPPED_BINARY
move idb files to DIR_UNSTRIPPED_IDB and DIR_STRIPPED_IDB
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


DIR_UNSTRIPPED_BINARY = './github-proj/binary'
DIR_STRIPPED_BINARY = './github-proj/binary-strip'
DIR_UNSTRIPPED_IDB = './github-proj/binary-idb'
DIR_STRIPPED_IDB = "./github-proj/binary-strip-idb"
IDA_PYTHON_SCRIPT = "./idascript/1_ext_idb_and_nameaddr/ext_func_name_and_addr_idapython.py"

IDA_IDB_DICT = {64:('ida64','.i64'), 32:("ida",".idb")}
threads = cpu_count()-6
IDA_TIMEOUT=60*120 # second
NOT_BINARY_SUFFIX = (".i64",".idb",".id0",".id1",".id2",".til",".nam",".json",".asm")
NAME_ADDR_JSON_SUFFIX = ".name_and_addr.json"
os.environ["NAME_ADDR_JSON_SUFFIX"] = NAME_ADDR_JSON_SUFFIX
# check strip command exist
cmd_exists = lambda x: any(os.access(os.path.join(path, x), os.X_OK) for path in os.environ["PATH"].split(os.pathsep))
assert cmd_exists('file.exe'), "file.exe not found in PATH"

def check_bit(binary):
    # use file command to check the bit of binary
    cmd = f"file {binary}"
    res = os.popen(cmd).read()
    if '32-bit' in res:
        return 32
    elif '64-bit' in res:
        return 64
    else:
        return None

def disassemble_path(bin_path):
    # get all file
    binaries = []
    for root, dirs, files in os.walk(bin_path):
        for name in files:
            if not name.endswith(NOT_BINARY_SUFFIX):
                binaries.append(os.path.join(root, name))
    print(f"[-] found {len(binaries)} binary files")
    # disassemble
    all_cnt = len(binaries)
    for idx,file in enumerate(binaries):
        try:
            bit = check_bit(file)
            IDA, IDB_SUFFIX = IDA_IDB_DICT[bit]
            if os.path.exists(file+IDB_SUFFIX):
                continue
            print(f'[-] {idx+1}/{all_cnt} Disassembling File {file}')
            cmd = f"{IDA} -A -S{IDA_PYTHON_SCRIPT} {file}"
            subprocess.run(cmd, shell=True, check=True, timeout=IDA_TIMEOUT, 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            logging.error(e)


def disassemble_one(file_queue, failed, thread_id):
    while not file_queue.empty():
        file = file_queue.get()
        remain_count = file_queue.qsize()
        try:
            bit = check_bit(file)
            IDA, IDB_SUFFIX = IDA_IDB_DICT[bit]
            if os.path.exists(file+IDB_SUFFIX) and os.path.exists(file+NAME_ADDR_JSON_SUFFIX):
                print(f'[t{thread_id}] remain {remain_count} file {file} already done')
                continue
            print(f'[t{thread_id}] remain {remain_count} disassembling file {file}')
            cmd = f"{IDA} -A -S{IDA_PYTHON_SCRIPT} {file}"
            subprocess.check_output(cmd, timeout=IDA_TIMEOUT)
            if not os.path.exists(file+IDB_SUFFIX) and not os.path.exists(file+NAME_ADDR_JSON_SUFFIX):
                raise Exception("idb or json not found")
        except Exception as e:
            print("[!]", e)
            failed.put(file+"\n"+str(e))

def multi_thread_main():
    # get all file
    binaries = []
    for root, dirs, files in os.walk(DIR_UNSTRIPPED_BINARY):
        if 'SRC' in dirs:
            dirs.remove('SRC')
        for name in files:
            if not name.endswith(NOT_BINARY_SUFFIX):
                binaries.append(os.path.join(root, name))
    if DIR_STRIPPED_BINARY:
        for root, dirs, files in os.walk(DIR_STRIPPED_BINARY):
            if 'SRC' in dirs:
                dirs.remove('SRC')
            for name in files:
                if not name.endswith(NOT_BINARY_SUFFIX):
                    binaries.append(os.path.join(root, name))
    print(f"[-] found {len(binaries)} binary files")
    # run 
    queue = Queue()
    failed = Queue()
    for f in binaries:
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
        f.write(f"[-] DIR_UNSTRIPPED_BINARY: {DIR_UNSTRIPPED_BINARY}\n")
        f.write(f"[-] DIR_STRIPPED_BINARY: {DIR_STRIPPED_BINARY}\n")
        f.write(f"[-] failed files count {failed.qsize()}\n")
        while not failed.empty():
            f.write(failed.get()+"\n")


def move_idb(bin_path, idb_path, delete_asm=False):
    idbs = []
    nameaddrs = []
    # get all idb file
    for root, dirs, files in os.walk(bin_path):
        for name in files:
            if name.endswith(('idb','.i64')):
                idbs.append(os.path.join(root, name))
            if name.endswith(NAME_ADDR_JSON_SUFFIX):
                nameaddrs.append(os.path.join(root, name))
            if delete_asm and name.endswith(".asm"):
                os.remove(os.path.join(root, name)) 
    # move idb
    for idb in tqdm(idbs,desc="move idb"):
        d = os.path.dirname(idb).replace(bin_path, idb_path)
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        dst = idb.replace(bin_path, idb_path)
        shutil.move(idb, dst)
    # move nameaddrs
    for idb in tqdm(nameaddrs,desc="move nameaddr"):
        d = os.path.dirname(idb).replace(bin_path, idb_path)
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        dst = idb.replace(bin_path, idb_path)
        shutil.move(idb, dst)

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

    move_idb(DIR_UNSTRIPPED_BINARY, DIR_UNSTRIPPED_IDB, delete_asm=True)
    move_idb(DIR_STRIPPED_BINARY, DIR_STRIPPED_IDB, delete_asm=True)
    print('[+] move idb files done')