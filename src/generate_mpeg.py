import json

from bloqade.qbraid.simulation_result import QuEraSimulationResult

json_data: dict =  json.loads(open("./data/simulation.json").read())
result = QuEraSimulationResult.from_json(json_data)

result.animate(save_mpeg=True, filename="simulation")