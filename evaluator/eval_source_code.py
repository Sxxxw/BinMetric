import subprocess
import logging
import uuid
import json
import os
'''
=========create docker container===========
docker create -it --name dockcrosstest dockcross/linux-x64:latest /bin/bash
docker start dockcrosstest
=============usage=====================
docker cp ./program.c dockcrosstest:/program.c
docker exec dockcrosstest gcc /program.c -o /program
docker exec -i dockcrosstest /program
'''

def check_container_stat(container_name):
    command = f"docker stats --no-stream --format json {container_name}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("[!] Error: check container stat failed")
        return None
    stat = json.loads(result.stdout)
    logging.debug(stat)
    return stat

def restart_container(container_name) -> bool:
    command = f"docker restart {container_name}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error("[!] Error: restart container failed")
        return False
    return True

def create_docker_container(container_name = "compile_run_container", 
                            docker_image = "dockcross/linux-x64:latest"):
    # check docker is installed
    check_process = subprocess.run(["docker", "--version"], capture_output=True, text=True)
    if check_process.returncode != 0:
        raise Exception("[!] Docker is not installed")
    # check container exists
    check_process = subprocess.run(["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"], capture_output=True, text=True)
    if check_process.returncode == 0:
        # Container already exists, start it
        subprocess.run(["docker", "start", container_name], capture_output=True, check=True)
        return container_name
    # Create a Docker container and keep it running
    subprocess.run(["docker", "run", "--name", container_name, "-dit", docker_image, "/bin/bash"], check=True)
    return container_name

def compile_and_run_c_code_in_docker(container_name: str, code: str, program_inputs: list, expected_outputs: list, timeout: int = 5):
    try:
        # Unique ID for the file name to avoid conflicts
        file_name = f"temp_{uuid.uuid4()}.c"
        with open(file_name, "w") as file:
            file.write(code)

        # Copy the C file to the container
        subprocess.run(["docker", "cp", file_name, f"{container_name}:/program.c"], capture_output=True, check=True)

        # Compile the C code inside the container
        subprocess.run(["docker", "exec", container_name, "gcc", "/program.c", "-o", "/program"], check=True)
    except subprocess.CalledProcessError as e:
        logging.debug(f"[!] Error during Docker operations:\n{e}")
        return 0
    finally:
        # Cleanup: remove the temporary file
        if os.path.exists(file_name):
            os.remove(file_name)

    # Run the compiled program
    results = []
    for program_input, expected_output in zip(program_inputs, expected_outputs):
        try:
            run_process = subprocess.run(
                ["docker", "exec", "-i", container_name, "/program"],
                input=program_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Check the output
            if run_process.returncode != 0:
                logging.debug(f"[!] Runtime Error: {run_process.stderr}")

            output = run_process.stdout
            if output.strip() == expected_output.strip():
                logging.debug("[+] Success: Output matches expected output") 
                results.append(1)
            else:
                logging.debug(f"[-] Failure: Output does not match. Expected '{expected_output}', got '{output}'") 
                results.append(0)
        except subprocess.TimeoutExpired:
            logging.debug("[-] Error: Program timeout")
            results.append(0)
    # Cleanup: remove the temporary file
    if os.path.exists(file_name):
        os.remove(file_name)
    return 1 if sum(results) == len(results) else 0

def compile_and_run_cpp_code_in_docker(container_name: str, code: str, program_inputs: list, expected_outputs: list, timeout: int = 5):
    try:
        # Unique ID for the file name to avoid conflicts
        file_name = f"temp_{uuid.uuid4()}.cpp"
        with open(file_name, "w") as file:
            file.write(code)

        # Copy the C++ file to the container
        subprocess.run(["docker", "cp", file_name, f"{container_name}:/program.cpp"], capture_output=True, check=True)

        # Compile the C++ code inside the container
        subprocess.run(["docker", "exec", container_name, "gcc", "/program.cpp", "-o", "/program"], check=True)
    except subprocess.CalledProcessError as e:
        logging.debug(f"[!] Error during Docker operations:\n{e}")
        return 0
    finally:
        # Cleanup: remove the temporary file
        if os.path.exists(file_name):
            os.remove(file_name)

    # Run the compiled program
    results = []
    for program_input, expected_output in zip(program_inputs, expected_outputs):
        try:
            run_process = subprocess.run(
                ["docker", "exec", "-i", container_name, "/program"],
                input=program_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Check the output
            if run_process.returncode != 0:
                logging.debug(f"[!] Runtime Error: {run_process.stderr}")

            output = run_process.stdout
            if output.strip() == expected_output.strip():
                logging.debug("[+] Success: Output matches expected output") 
                results.append(1)
            else:
                logging.debug(f"[-] Failure: Output does not match. Expected '{expected_output}', got '{output}'") 
                results.append(0)
        except subprocess.TimeoutExpired:
            logging.debug("[-] Error: Program timeout")
            results.append(0)
    # Cleanup: remove the temporary file
    if os.path.exists(file_name):
        os.remove(file_name)
    return 1 if sum(results) == len(results) else 0

def compile_and_run_python_code_in_docker(container_name: str, code: str, program_inputs: list, expected_outputs: list, timeout: int = 5):
    try:
        # Unique ID for the file name to avoid conflicts
        file_name = f"temp_{uuid.uuid4()}.py"
        with open(file_name, "w") as file:
            file.write(code)

        # Copy the Python file to the container
        subprocess.run(["docker", "cp", file_name, f"{container_name}:/program.py"], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.debug(f"[!] Error during Docker operations:\n{e}")
        return 0
    finally:
        # Cleanup: remove the temporary file
        if os.path.exists(file_name):
            os.remove(file_name)

    # Run the compiled program
    results = []
    for program_input, expected_output in zip(program_inputs, expected_outputs):
        try:
            run_process = subprocess.run(
                ["docker", "exec", "-i", container_name, "python", "/program.py"],
                input=program_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Check the output
            if run_process.returncode != 0:
                logging.debug(f"[!] Runtime Error: {run_process.stderr}")

            output = run_process.stdout
            if output.strip() == expected_output.strip():
                logging.debug("[+] Success: Output matches expected output") 
                results.append(1)
            else:
                logging.debug(f"[-] Failure: Output does not match. Expected '{expected_output}', got '{output}'") 
                results.append(0)
        except subprocess.TimeoutExpired:
            logging.debug("[-] Error: Program timeout")
            results.append(0)
    # Cleanup: remove the temporary file
    if os.path.exists(file_name):
        os.remove(file_name)
    return 1 if sum(results) == len(results) else 0


def compile_and_run_JS_code_in_docker(container_name: str, code: str, program_inputs: list, expected_outputs: list, timeout: int = 5):
    try:
        # Unique ID for the file name to avoid conflicts
        file_name = f"temp_{uuid.uuid4()}.js"
        with open(file_name, "w") as file:
            file.write(code)

        # Copy the Python file to the container
        subprocess.run(["docker", "cp", file_name, f"{container_name}:/program.js"], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logging.debug(f"[!] Error during Docker operations:\n{e}")
        return 0
    finally:
        # Cleanup: remove the temporary file
        if os.path.exists(file_name):
            os.remove(file_name)

    # Run the compiled program
    results = []
    for program_input, expected_output in zip(program_inputs, expected_outputs):
        try:
            run_process = subprocess.run(
                ["docker", "exec", "-i", container_name, "node", "/program.js"],
                input=program_input,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # Check the output
            if run_process.returncode != 0:
                logging.debug(f"[!] Runtime Error: {run_process.stderr}")

            output = run_process.stdout
            if output.strip() == expected_output.strip():
                logging.debug("[+] Success: Output matches expected output") 
                results.append(1)
            else:
                logging.debug(f"[-] Failure: Output does not match. Expected '{expected_output}', got '{output}'") 
                results.append(0)
        except subprocess.TimeoutExpired:
            logging.debug("[-] Error: Program timeout")
            results.append(0)
    # Cleanup: remove the temporary file
    if os.path.exists(file_name):
        os.remove(file_name)
    return 1 if sum(results) == len(results) else 0


if __name__ == "__main__":
    # Create the Docker container
    container_name = create_docker_container(container_name = "dockcrosstest", docker_image = "dockcross/linux-x64:latest")
    # Example usage
    import jsonlines
    from tqdm import tqdm
    logging.basicConfig(level=logging.INFO)
    def write_jsonline_file(file_path, data):
        with jsonlines.open(file_path, 'a') as writer:
            writer.write(data)
    jsonl_path = "/data/chenye/PythonProjects/BinCodeLM-Eval/RefCode/data1.jsonl"
    js_ok_jsonl_path = "/data/chenye/PythonProjects/BinCodeLM-Eval/RefCode/data1_js_ok.jsonl"
    js_fail_jsonl_path = "/data/chenye/PythonProjects/BinCodeLM-Eval/RefCode/data1_js_fail.jsonl"
    js_codes_ok = []
    js_codes_fail = []
    with jsonlines.open(jsonl_path) as reader:
        dataset = list(reader)
    for obj in tqdm(dataset):
        if obj["type"] == "JavaScript":
            code = obj["code"]
            test_case = obj["test_case"]
            program_inputs = [t[0] for t in test_case]
            expected_outputs = [t[1] for t in test_case]
            result = compile_and_run_JS_code_in_docker(container_name, code, program_inputs, expected_outputs)
            if result == 1:
                # js_codes_ok.append(code)
                write_jsonline_file(js_ok_jsonl_path,obj)
            elif result == 0:
                # js_codes_fail.append(code)
                write_jsonline_file(js_fail_jsonl_path,obj)