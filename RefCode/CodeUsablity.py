# main.py
import os
import json
from tqdm import tqdm
import subprocess
import execjs

def handle_c(json_obj):
# def cpp_compile_and_run(temp_cpp_path, binary_path, input_data):
    code, binary_path, io_data = json_obj['code'], './temp', json_obj['test_case']
    with open("temp.c", "w", encoding='utf-8') as temp_c_file:
        temp_c_file.write(code)
    for input_data, expected_output in io_data:
        try:
            # 编译CPP文件，设置超时时间为1秒
            subprocess.run(['gcc', './temp.c', '-o', binary_path], 
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
            # print('1')
            if os.path.exists(binary_path):
                run_process = subprocess.run([f"./{binary_path}"], input=input_data, text=True, capture_output=True, check=True, timeout=2)
                return run_process.stdout.strip() == expected_output.strip()
            else:
                return False
        except subprocess.TimeoutExpired:
            pass
        except subprocess.CalledProcessError as e:
            pass
        except Exception as e:
            pass
        finally:
            if os.path.exists('./temp.c'):
                os.remove('./temp.c')
            if os.path.exists(binary_path):
                os.remove(binary_path)
        return False

def handle_cpp(json_obj):

    code, binary_path, io_data = json_obj['code'], './temp', json_obj['test_case']
    with open("temp.cpp", "w", encoding='utf-8') as temp_cpp_file:
        temp_cpp_file.write(code)
    for input_data, expected_output in io_data:
        try:
            subprocess.run(['g++', './temp.cpp', '-o', binary_path], 
                        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
            if os.path.exists(binary_path):
                run_process = subprocess.run([f"{binary_path}"], input=input_data, text=True, capture_output=True, check=True, timeout=2)
                # print(run_process.stdout.strip(), '\n', expected_output.strip())
                return run_process.stdout.strip() == expected_output.strip()
            else:
                return False
        except subprocess.TimeoutExpired:
            pass
        except subprocess.CalledProcessError as e:
            pass
        except Exception as e:
            pass
        finally:
            if os.path.exists('./temp.cpp'):
                os.remove('./temp.cpp')
            if os.path.exists(binary_path):
                os.remove(binary_path)
        return False

def handle_js(json_obj):
    # 获取代码和测试用例
    code = json_obj.get("code", "")
    test_cases = json_obj.get("test_case", [])

    ctx = execjs.compile(code)

    # 对每个测试用例进行检查
    for test_input, expected_output in test_cases:
        try:
            # 运行代码并传入测试输入
            actual_output = ctx.eval(f'({test_input})')
            
            # 比较实际输出和预期输出
            if json.dumps(actual_output) != json.dumps(expected_output):
                return False
        except:
            # print(f"JavaScript code error with input {test_input}: {e}")
            return False
    del ctx

    return True

def process_jsonl_file(input_file_path, output_file_path):
    with open(input_file_path, 'r') as file, open(output_file_path, 'a') as output_file:
        total = len(file.readlines())
        file.seek(0)
        for line in tqdm(file.readlines(), total=total):
            json_obj = json.loads(line)
            is_usable = False
            if json_obj['type'] == 'C':
                is_usable = handle_c(json_obj)
            elif json_obj['type'] == 'C++':
                is_usable = handle_cpp(json_obj)
            elif json_obj['type'] == 'JavaScript':
                is_usable = handle_js(json_obj)
            else:
                print(f"Unknown type: {json_obj['type']}")
            # print(is_usable)
            
            if is_usable:
                # print('1')
                output_file.write(f"{line}")
                output_file.flush()

process_jsonl_file('data1.jsonl', 'data_o.jsonl')
