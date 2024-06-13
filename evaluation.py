import json
import fire
import logging
from evaluator.evaluator_ori import evaluate_correctness

def main(
    prediction_file: str,
    problem_file: str,
    timeout: float = 5.0,
    v: bool = False, # debug
    ):

    if v:
        logging.basicConfig(level=logging.DEBUG)

    results = evaluate_correctness(prediction_file, problem_file, timeout)
    print(prediction_file)
    print(json.dumps(results,indent=4))


if __name__ == "__main__":
    fire.Fire(main)