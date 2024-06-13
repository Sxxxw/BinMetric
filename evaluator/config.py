PROMPT_TEMPLATE = {
    "DEFAULT": "{instruction}\n{input}",

    "CSR": "",

    "DEC": "### Instruction: Please Imagine you are an experienced binary reverse engineer. The following is a disassembled assembly code, your task is to understand it and output its corresponding C source code, wrapped in three backticks (```), do not explain. \n{example}Input assembly code: \n```\n{input}\n```\n ### Response:\n",

    "SR": "### Instruction: Please imagine you are an experienced binary reverse engineer. The following is a stripped decompiled C function, your task is to understand it and output the descriptive function signature in its corresponding source code. This includes the function name, parameter list and its type, and return value type. Wrap the output with three backticks (```), do not explain. \n{example}Input decompiled C function:  \n```C\n{input}\n```\n ### Response:\n",

    "BCS": "### Instruction: Please imagine you are an experienced binary reverse engineer. The following is a stripped decompiled C function, your task is to understand it and generate a short comment to the function describing its functionality. No more than 96 words. \n{example}Input decompiled C function:  \n```C\n{input}\n```\n ### Response:\n",

    "AC": "",

    "AIG": "{instruction}\n{input}",
}

TASKTYPE_EVALUATOR_DICT = {
    "CSR": "SemanticComprehensionEvaluator",
    "DEC": "BinaryLiftingEvaluator",
    "SR": "SemanticComprehensionEvaluator",
    "BCS": "SemanticComprehensionEvaluator",
    "AC": "LogicalAnalysisEvaluator",
    "AIG": "AssemblySynthesisEvaluator"
}

# functions defined in queryllm/utils.py
TASKTYPE_POSTPROCESS_DICT = {
    "CSR": "parse_code_in_block",
    "DEC": "parse_code_in_block",
    "SR": "parse_code_in_block",
    "BCS": "save_all_generated",
    "AC": "parse_code_in_block",
    "AIG": "parse_code_in_block"
}