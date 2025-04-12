import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union

@dataclass
class Instruction:
    type: str
    id: int
    begin_time: Union[int, float]
    end_time: Union[int, float]
    # Additional fields that vary by instruction type are stored in 'details'
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Instruction":
        # Extract common fields
        inst_type = d.get("type")
        inst_id = d.get("id")
        begin_time = d.get("begin_time")
        end_time = d.get("end_time")
        # The remaining keys are stored in details
        details = {k: v for k, v in d.items() if k not in {"type", "id", "begin_time", "end_time"}}
        return cls(
            type=inst_type,
            id=inst_id,
            begin_time=begin_time,
            end_time=end_time,
            details=details
        )

@dataclass
class JobData:
    name: str
    architecture_spec_path: str
    instructions: List[Instruction] = field(default_factory=list)
    runtime: Union[int, float] = 0

    @classmethod
    def from_json(cls, json_source: Union[str, Dict[str, Any]]) -> "JobData":
        """
        Creates a JobData instance from a JSON string or a dictionary.
        """
        if isinstance(json_source, str):
            data = json.loads(json_source)
        else:
            data = json_source

        instructions = [Instruction.from_dict(inst) for inst in data.get("instructions", [])]
        return cls(
            name=data.get("name", ""),
            architecture_spec_path=data.get("architecture_spec_path", ""),
            instructions=instructions,
            runtime=data.get("runtime", 0)
        )

import argparse
# Example usage:
parser = argparse.ArgumentParser(description="Load job data from JSON.")
parser.add_argument(
    "json_file",
    type=str,
    nargs="?",
    default="./data/zac_code.json",
    help="Path to the JSON file containing job data."
)
args = parser.parse_args()

if __name__ == "__main__":
    json_str = open(args.json_file).read()
    
    job_data = JobData.from_json(json_str)
    print("Job name:", job_data.name)
    print("Architecture spec path:", job_data.architecture_spec_path)
    print("Runtime:", job_data.runtime)
    print("Instructions:")
    for inst in job_data.instructions:
        print("  -", inst)