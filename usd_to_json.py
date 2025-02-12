from pxr import Usd, UsdUtils
import json

def usd_to_json(usd_file, json_file):
    # Load the USD stage
    stage = Usd.Stage.Open(usd_file)
    
    # Convert USD stage to dictionary
    usd_dict = UsdUtils.StageToDict(stage)
    
    # Write to JSON
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(usd_dict, f, indent=4)
    
    print(f"✅ Converted {usd_file} to {json_file}")

# Example usage
usd_to_json("usd/animation.usd", "usd/output.json")
