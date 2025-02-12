import unreal

# Path to the Skeletal Mesh (Change this to your actual asset path)
skeletal_mesh_path = "/Game/Characters/remapped_alien"
skeletal_mesh = unreal.EditorAssetLibrary.load_asset(skeletal_mesh_path)

# DAZ to ARKit Blendshape Mapping
morph_mapping = {
    "Jaw Right": "jawRight",
    "Jaw Open": "jawOpen",
    "Jaw Left": "jawLeft",
    "Jaw Forward": "jawForward",
    "Eye Wide Right": "eyeWideRight",
    "Eye Wide Left": "eyeWideLeft",
    "Eye Blink Right": "eyeBlinkRight",
    "Eye Blink Left": "eyeBlinkLeft",
    "facs_ctrl_EyeLookUpRight": "eyeLookUpRight",
    "facs_ctrl_EyeLookUpLeft": "eyeLookUpLeft",
    "facs_ctrl_EyeLookOutRight": "eyeLookOutRight",
    "facs_ctrl_EyeLookOutLeft": "eyeLookOutLeft",
    "facs_ctrl_EyeLookInRight": "eyeLookInRight",
    "facs_ctrl_EyeLookInLeft": "eyeLookInLeft",
    "facs_ctrl_EyeLookDownRight": "eyeLookDownRight",
    "facs_ctrl_EyeLookDownLeft": "eyeLookDownLeft",
    "Cheek Puff": "cheekPuff",
    "Brow Inner Up": "browInnerUp",
    "Tongue Out": "tongueOut",
    "Nose Sneer Right": "noseSneerRight",
    "Nose Sneer Left": "noseSneerLeft",
    "Mouth Upper Up Right": "mouthUpperUpRight",
    "Mouth Upper Up Left": "mouthUpperUpLeft",
    "Mouth Stretch Right": "mouthStretchRight",
    "Mouth Stretch Left": "mouthStretchLeft",
    "Mouth Smile Right": "mouthSmileRight",
    "Mouth Smile Left": "mouthSmileLeft",
    "Mouth Shrug Upper": "mouthShrugUpper",
    "Mouth Shrug Lower": "mouthShrugLower",
    "Mouth Roll Upper": "mouthRollUpper",
    "Mouth Roll Lower": "mouthRollLower",
    "Mouth Right": "mouthRight",
    "Mouth Left": "mouthLeft",
    "Mouth Pucker": "mouthPucker",
    "Mouth Press Right": "mouthPressRight",
    "Mouth Press Left": "mouthPressLeft",
    "Mouth Lower Down Right": "mouthLowerDownRight",
    "Mouth Lower Down Left": "mouthLowerDownLeft",
    "Mouth Funnel": "mouthFunnel",
    "Mouth Frown Right": "mouthFrownRight",
    "Mouth Frown Left": "mouthFrownLeft",
    "Mouth Dimple Right": "mouthDimpleRight",
    "Mouth Dimple Left": "mouthDimpleLeft",
    "Mouth Close": "mouthClose",
    "Eye Squint Right": "eyeSquintRight",
    "Eye Squint Left": "eyeSquintLeft",
    "Cheek Squint Right": "cheekSquintRight",
    "Cheek Squint Left": "cheekSquintLeft",
    "Brow Outer Up Right": "browOuterUpRight",
    "Brow Outer Up Left": "browOuterUpLeft",
    "Brow Down Right": "browDownRight",
    "Brow Down Left": "browDownLeft"
}

if skeletal_mesh:
    # Get all Morph Targets
    morph_targets = skeletal_mesh.get_editor_property("morph_targets")

    if morph_targets:
        unreal.log(f"Found {len(morph_targets)} Morph Targets in {skeletal_mesh_path}")

        for morph in morph_targets:
            original_name = morph.get_name()
            
            if original_name in morph_mapping:
                new_name = morph_mapping[original_name]

                # Use Unreal's Rename function to modify the morph target name
                success = morph.rename(new_name)

                if success:
                    unreal.log(f"✅ Renamed {original_name} to {new_name}")
                else:
                    unreal.log(f"❌ Failed to rename {original_name}")

        # Save the Skeletal Mesh
        unreal.EditorAssetLibrary.save_asset(skeletal_mesh_path)
        unreal.log("✅ Morph renaming completed and saved!")
    else:
        unreal.log_error("❌ No Morph Targets found in this Skeletal Mesh.")
else:
    unreal.log_error(f"❌ Failed to load Skeletal Mesh at {skeletal_mesh_path}.")
