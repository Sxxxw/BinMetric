from capstone import *
from unicorn import *
from unicorn.x86_const import *
from unicorn.arm_const import *
from unicorn.mips_const import *
from keystone import *
import logging
from typing import Literal

start_address = 0x0

def hook_mem_invalid(uc, access, address, size, value, user_data):
    if access == UC_MEM_READ_UNMAPPED:
        logging.debug("Trying to read from unmapped memory at 0x%x" % address)
    elif access == UC_MEM_WRITE_UNMAPPED:
        logging.debug("Trying to write to unmapped memory at 0x%x" % address)
    return False

def run_x86_assmbly_code(code,program_inputs,expected_outputs):
    uc = Uc(UC_ARCH_X86,UC_MODE_32)
    ks = Ks(KS_ARCH_X86,KS_MODE_32)
    uc.hook_add(UC_HOOK_MEM_READ_UNMAPPED | UC_HOOK_MEM_WRITE_UNMAPPED, hook_mem_invalid)
    byte_stream,_ = ks.asm(code)
    byte_stream = bytes(byte_stream)
    uc.mem_map(start_address, 2*1024*1024)
    uc.mem_write(start_address, byte_stream)
    uc.reg_write(UC_X86_REG_EBP,0x1000)
    uc.reg_write(UC_X86_REG_ESP,0x1000)
    program_inputs = [inputs.split(" ") for inputs in program_inputs]
    for i in range(len(program_inputs)):
            for j in range(len(program_inputs[i])):
                program_inputs[i][j] = int(program_inputs[i][j],16)
    for i in range(len(expected_outputs)):
        if len(program_inputs[i]) == 4:
            expected_outputs[i] = expected_outputs[i].split(" ")
            for j in range(len(expected_outputs[i])):
                expected_outputs[i][j] = int(expected_outputs[i][j])
        else:
            continue
    results = []
    for program_input, expected_output in zip(program_inputs, expected_outputs):
        if len(program_input) == 4:
            uc.reg_write(UC_X86_REG_EAX,program_input[0])
            uc.reg_write(UC_X86_REG_EBX,program_input[1])
            uc.reg_write(UC_X86_REG_ECX,program_input[2])
            uc.reg_write(UC_X86_REG_EDX,program_input[3])
            try:
                uc.emu_start(start_address, start_address + len(byte_stream))
                eax = uc.reg_read(UC_X86_REG_EAX)
                ebx = uc.reg_read(UC_X86_REG_EBX)
                ecx = uc.reg_read(UC_X86_REG_ECX)
                edx = uc.reg_read(UC_X86_REG_EDX)
                if(eax==expected_output[0] and ebx==expected_output[1] and ecx==expected_output[2] and edx==expected_output[3]):
                    logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                    results.append(1)
                else:
                    logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected eax:{expected_output[0]} ebx:{expected_output[1]} ecx:{expected_output[2]} edx:{expected_output[3]},got eax:{eax} ebx:{ebx} ecx:{ecx} edx:{edx}")
                    results.append(0)
            except UcError as e:
                logging.error("ERROR: %s at 0x%x" % (e, uc.reg_read(UC_X86_REG_EIP)))
        else:
            uc.emu_start(start_address, start_address + len(byte_stream))
            if isinstance(expected_output,int) or isinstance(expected_output,list):
                ls=[]
                for i in range(0,program_input[1],4):
                    ls.append(int.from_bytes(uc.mem_read(program_input[0]+i,4),byteorder="little"))
                if program_input[1] == 4:
                    if [expected_output] == ls:
                        logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                        results.append(1)
                    else:
                        logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{ls[0]}")
                        results.append(0)
                else:
                    if expected_output == ls:
                        logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                        results.append(1)
                    else:
                        logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{ls}")
                        results.append(0)
            elif isinstance(expected_output,str):
                string = ""
                for i in range(program_input[1]):
                    string += uc.mem_read(program_input[0]+i,1).decode()
                if string == expected_output:
                    logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                    results.append(1)
                else:
                    logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{string}")
                    results.append(0)
    return 1 if sum(results) == len(results) else 0

def run_x64_assmbly_code(code,program_inputs,expected_outputs):
    uc = Uc(UC_ARCH_X86,UC_MODE_64)
    ks = Ks(KS_ARCH_X86,KS_MODE_64)
    uc.hook_add(UC_HOOK_MEM_READ_UNMAPPED | UC_HOOK_MEM_WRITE_UNMAPPED, hook_mem_invalid)
    byte_stream,_ = ks.asm(code)
    byte_stream = bytes(byte_stream)
    uc.mem_map(start_address, 2*1024*1024)
    uc.mem_write(start_address, byte_stream)
    program_inputs = [inputs.split(" ") for inputs in program_inputs]
    uc.reg_write(UC_X86_REG_RBP,0x1000)
    uc.reg_write(UC_X86_REG_RSP,0x1000)
    for i in range(len(program_inputs)):
            for j in range(len(program_inputs[i])):
                program_inputs[i][j] = int(program_inputs[i][j],16)
    for i in range(len(expected_outputs)):
        if len(program_inputs[i]) == 4:
            expected_outputs[i] = expected_outputs[i].split(" ")
            for j in range(len(expected_outputs[i])):
                expected_outputs[i][j] = int(expected_outputs[i][j],16)
        else:
            continue
    results = []
    for program_input, expected_output in zip(program_inputs, expected_outputs):
        if len(program_input) == 4:
            uc.reg_write(UC_X86_REG_RAX,program_input[0])
            uc.reg_write(UC_X86_REG_RBX,program_input[1])
            uc.reg_write(UC_X86_REG_RCX,program_input[2])
            uc.reg_write(UC_X86_REG_RDX,program_input[3])
            try:
                uc.emu_start(start_address, start_address + len(byte_stream))
                rax = uc.reg_read(UC_X86_REG_RAX)
                rbx = uc.reg_read(UC_X86_REG_RBX)
                rcx = uc.reg_read(UC_X86_REG_RCX)
                rdx = uc.reg_read(UC_X86_REG_RDX)
                if(rax==expected_output[0] and rbx==expected_output[1] and rcx==expected_output[2] and rdx==expected_output[3]):
                    logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                    results.append(1)
                else:
                    logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected rax:{expected_output[0]} rbx:{expected_output[1]} rcx:{expected_output[2]} rdx:{expected_output[3]},got rax:{rax} rbx:{rbx} rcx:{rcx} rdx:{rdx}")
                    results.append(0)
            except UcError as e:
                logging.error("ERROR: %s at 0x%x" % (e, uc.reg_read(UC_X86_REG_RIP)))
        else:
            uc.emu_start(start_address, start_address + len(byte_stream))
            if isinstance(expected_output,int) or isinstance(expected_output,list):
                ls=[]
                for i in range(0,program_input[1],4):
                    temp = uc.mem_read(program_input[0]+i,4)
                    ls.append(int.from_bytes(temp,byteorder="little"))
                if program_input[1] == 4:
                    if [expected_output] == ls:
                        logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                        results.append(1)
                    else:
                        logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{ls[0]}")
                        results.append(0)
                else:
                    if expected_output == ls:
                        logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                        results.append(1)
                    else:
                        logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{ls}")
                        results.append(0)
            elif isinstance(expected_output,str):
                string = ""
                for i in range(program_input[1]):
                    string += uc.mem_read(program_input[0]+i,1).decode()
                if string == expected_output:
                    logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                    results.append(1)
                else:
                    logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{string}")
                    results.append(0)
    return 1 if sum(results) == len(results) else 0

def run_arm32_assmbly_code(code,program_inputs,expected_outputs):
    uc = Uc(UC_ARCH_ARM,UC_MODE_ARM)
    ks = Ks(KS_ARCH_ARM,KS_MODE_ARM)
    uc.hook_add(UC_HOOK_MEM_READ_UNMAPPED | UC_HOOK_MEM_WRITE_UNMAPPED, hook_mem_invalid)
    byte_stream,_ = ks.asm(code)
    byte_stream = bytes(byte_stream)
    uc.mem_map(start_address, 2*1024*1024)
    uc.mem_write(start_address, byte_stream)
    program_inputs = [inputs.split(" ") for inputs in program_inputs]
    uc.reg_write(UC_ARM_REG_SP,0x1000)
    uc.reg_write(UC_ARM_REG_LR,0xdeadbeef)
    for i in range(len(program_inputs)):
            for j in range(len(program_inputs[i])):
                program_inputs[i][j] = int(program_inputs[i][j],16)
    for i in range(len(expected_outputs)):
        if len(program_inputs[i]) == 4:
            expected_outputs[i] = expected_outputs[i].split(" ")
            for j in range(len(expected_outputs[i])):
                expected_outputs[i][j] = int(expected_outputs[i][j])
        else:
            continue
    results = []
    for program_input, expected_output in zip(program_inputs, expected_outputs):
        if len(program_input) == 4:
            uc.reg_write(UC_ARM_REG_R0,program_input[0])
            uc.reg_write(UC_ARM_REG_R1,program_input[1])
            uc.reg_write(UC_ARM_REG_R2,program_input[2])
            uc.reg_write(UC_ARM_REG_R3,program_input[3])
            try:
                uc.emu_start(start_address, start_address + len(byte_stream))
                r0 = uc.reg_read(UC_ARM_REG_R0)
                r1 = uc.reg_read(UC_ARM_REG_R1)
                r2 = uc.reg_read(UC_ARM_REG_R2)
                r3 = uc.reg_read(UC_ARM_REG_R3)
                if(r0==expected_output[0] and r1==expected_output[1] and r2==expected_output[2] and r3==expected_output[3]):
                    logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                    results.append(1)
                else:
                    logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected r0:{expected_output[0]} r1:{expected_output[1]} r2:{expected_output[2]} r3:{expected_output[3]},got r0:{r0} r1:{r1} r2:{r2} r3:{r3}")
                    results.append(0)
            except UcError as e:
                logging.error("ERROR: %s at 0x%x" % (e, uc.reg_read(UC_ARM_REG_R15)))
        else:
            uc.emu_start(start_address, start_address + len(byte_stream))
            if isinstance(expected_output,int) or isinstance(expected_output,list):
                ls=[]
                for i in range(0,program_input[1],4):
                    temp = uc.mem_read(program_input[0]+i,4)
                    ls.append(int.from_bytes(temp,byteorder="little"))
                if program_input[1] == 4:
                    if [expected_output] == ls:
                        logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                        results.append(1)
                    else:
                        logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{ls[0]}")
                        results.append(0)
                else:
                    if expected_output == ls:
                        logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                        results.append(1)
                    else:
                        logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{ls}")
                        results.append(0)
            elif isinstance(expected_output,str):
                string = ""
                for i in range(program_input[1]):
                    string += uc.mem_read(program_input[0]+i,1).decode()
                if string == expected_output:
                    logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                    results.append(1)
                else:
                    logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{string}")
                    results.append(0)
    return 1 if sum(results) == len(results) else 0

def run_mips32_assmbly_code(code,program_inputs,expected_outputs):
    uc = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32)
    ks = Ks(KS_ARCH_MIPS,KS_MODE_MIPS32)
    uc.hook_add(UC_HOOK_MEM_READ_UNMAPPED | UC_HOOK_MEM_WRITE_UNMAPPED, hook_mem_invalid)
    byte_stream,_ = ks.asm(code)
    byte_stream = bytes(byte_stream)
    uc.mem_map(start_address, 2*1024*1024)
    uc.mem_write(start_address, byte_stream)
    program_inputs = [inputs.split(" ") for inputs in program_inputs]
    uc.reg_write(UC_MIPS_REG_SP,0x1000)
    for i in range(len(program_inputs)):
            for j in range(len(program_inputs[i])):
                program_inputs[i][j] = int(program_inputs[i][j],16)
    for i in range(len(expected_outputs)):
        if len(program_inputs[i]) == 4:
            expected_outputs[i] = expected_outputs[i].split(" ")
            for j in range(len(expected_outputs[i])):
                expected_outputs[i][j] = int(expected_outputs[i][j])
        else:
            continue
    results = []
    for program_input, expected_output in zip(program_inputs, expected_outputs):
        if len(program_input) == 4:
            uc.reg_write(UC_MIPS_REG_S0,program_input[0])
            uc.reg_write(UC_MIPS_REG_S1,program_input[1])
            uc.reg_write(UC_MIPS_REG_S2,program_input[2])
            uc.reg_write(UC_MIPS_REG_S3,program_input[3])
            try:
                uc.emu_start(start_address, start_address + len(byte_stream))
                reg_s0 = uc.reg_read(UC_MIPS_REG_S0)
                reg_s1 = uc.reg_read(UC_MIPS_REG_S1)
                reg_s2 = uc.reg_read(UC_MIPS_REG_S2)
                reg_s3 = uc.reg_read(UC_MIPS_REG_S3)
                if(reg_s0==expected_output[0] and reg_s1==expected_output[1] and reg_s2==expected_output[2] and reg_s3==expected_output[3]):
                    logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                    results.append(1)
                else:
                    logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected reg_s0:{expected_output[0]} reg_s1:{expected_output[1]} reg_s2:{expected_output[2]} reg_s3:{expected_output[3]},got reg_s0:{reg_s0} reg_s1:{reg_s1} reg_s2:{reg_s2} reg_s3:{reg_s3}")
                    results.append(0)
            except UcError as e:
                logging.error("ERROR: %s at 0x%x" % (e, uc.reg_read(UC_MIPS_REG_PC)))
        else:
            uc.emu_start(start_address, start_address + len(byte_stream))
            if isinstance(expected_output,int) or isinstance(expected_output,list):
                ls=[]
                for i in range(0,program_input[1],4):
                    temp = uc.mem_read(program_input[0]+i,4)
                    ls.append(int.from_bytes(temp,byteorder="little"))
                if program_input[1] == 4:
                    if [expected_output] == ls:
                        logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                        results.append(1)
                    else:
                        logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{ls[0]}")
                        results.append(0)
                else:
                    if expected_output == ls:
                        logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                        results.append(1)
                    else:
                        logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{ls}")
                        results.append(0)
            elif isinstance(expected_output,str):
                string = ""
                for i in range(program_input[1]):
                    string += uc.mem_read(program_input[0]+i,1).decode()
                if string == expected_output:
                    logging.debug("DEBUG:root:[+] Success: Output matches expected output.")
                    results.append(1)
                else:
                    logging.debug(f"DEBUG:root:[-] Failure: Output does not match. Expected mem_content:{expected_output},got mem_content:{string}")
                    results.append(0)
    return 1 if sum(results) == len(results) else 0