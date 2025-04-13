import json

from bloqade.qbraid.simulation_result import QuEraSimulationResult

def generate_mpeg(json_filename: str):
    # Load the simulation result from a JSON file
    json_data: dict = json.loads(open(json_filename).read())
    result = QuEraSimulationResult.from_json(json_data)
    
    # Generate the mpeg file
    filename: str = json_filename.split("/")[-1].split(".")[0]
    print(f"[i] Generating mpeg file: {filename}.mpeg")
    result.animate(save_mpeg=True, filename=filename, dilation_rate=1)


if __name__ == "__main__":
    generate_mpeg("./data/simulation.json")