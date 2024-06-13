import subprocess
import logging
import uuid
import json
import os

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

def compile_and_run_x64_assembly_code_in_docker(container_name: str, code: str, program_inputs: list, expected_outputs: list, timeout: int = 5):
    results = {"syntax_correct":0, "execution_correct":0}
    try:
        # Unique ID for the file name to avoid conflicts
        file_name = f"temp_{uuid.uuid4()}.s"
        with open(file_name, "w") as file:
            file.write(code)

        # Copy the C file to the container
        subprocess.run(["docker", "cp", file_name, f"{container_name}:/program.s"], capture_output=True, check=True)
        # Compile the C code inside the container
        subprocess.run(["docker", "exec", container_name, "gcc", "/program.s", "-o", "/program", "-z", "noexecstack","-lm"], check=True)
    except subprocess.CalledProcessError as e:
        logging.debug(f"[!] Error during Docker operations:\n{e}")
        return results
    finally:
        # Cleanup: remove the temporary file
        if os.path.exists(file_name):
            os.remove(file_name)
    results["syntax_correct"] = 1

    # Run the compiled program
    execution_results = []
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
                logging.debug(f"[+] Success: Output matches expected output") 
                execution_results.append(1)
            else:
                logging.debug(f"[-] Failure: Output does not match. Expected '{expected_output}', got '{output}'") 
                execution_results.append(0)
        except subprocess.TimeoutExpired:
            logging.debug("[-] Error: Program timeout")
            execution_results.append(0)
    # Cleanup: remove the temporary file
    if os.path.exists(file_name):
        os.remove(file_name)
    if sum(execution_results) == len(execution_results) :
        results["execution_correct"] = 1
    return results


def compile_and_run_x86_assembly_code_in_docker(container_name: str, code: str, program_inputs: list, expected_outputs: list, timeout: int = 5):
    try:
        # Unique ID for the file name to avoid conflicts
        file_name = f"temp_{uuid.uuid4()}.s"
        with open(file_name, "w") as file:
            file.write(code)

        # Copy the x86 file to the container
        subprocess.run(["docker", "cp", file_name, f"{container_name}:/program.s"], capture_output=True, check=True)

        # Compile the x86 assembly code inside the container
        subprocess.run(["docker", "exec", container_name, "gcc", "-m32", "/program.s", "-o", "/program", "-z", "noexecstack"], check=True)
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