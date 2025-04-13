import json

def fix_simulation(json_file: str):
    json_data: dict = json.loads(open(json_file).read())
    
    assert "atom_animation_state" in json_data, "No atom_animation_state found in the JSON file."
    
    atom_animation_state = json_data["atom_animation_state"]
    assert "qpu_fov" in atom_animation_state, "No atoms found in the atom_animation_state."
    
    # Fix the atom_animation_state
    fixed_qpu_fov = atom_animation_state["qpu_fov"]
    if "xmin" not in fixed_qpu_fov or fixed_qpu_fov["xmin"] is None:
        fixed_qpu_fov["xmin"] = 0
    if "xmax" not in fixed_qpu_fov or fixed_qpu_fov["xmax"] is None:
        fixed_qpu_fov["xmax"] = 10
    if "ymin" not in fixed_qpu_fov or fixed_qpu_fov["ymin"] is None:
        fixed_qpu_fov["ymin"] = 0
    if "ymax" not in fixed_qpu_fov or fixed_qpu_fov["ymax"] is None:
        fixed_qpu_fov["ymax"] = 10
        
    
    atom_animation_state["qpu_fov"] = fixed_qpu_fov
    json_data["atom_animation_state"] = atom_animation_state
    
    # Save the fixed JSON data
    with open(json_file, "w") as f:
        json.dump(json_data, f, indent=4)
        

if __name__ == "__main__":
    fix_simulation("./data/simulation.json")