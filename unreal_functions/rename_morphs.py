import unreal as ue

# Select the first Skeletal Mesh in the Content Browser
editor_util = ue.EditorUtilityLibrary()
selected_assets = editor_util.get_selected_assets()

if not selected_assets:
    ue.log_error("❌ No Skeletal Mesh selected!")
else:
    skeletal_mesh = selected_assets[0]  # Take the first selected mesh

    if not isinstance(skeletal_mesh, ue.SkeletalMesh):
        ue.log_error(f"❌ {skeletal_mesh.get_name()} is not a Skeletal Mesh!")
    else:
        morph_targets = skeletal_mesh.get_editor_property("morph_targets")

        if not morph_targets:
            ue.log_error(f"❌ No Morph Targets found in {skeletal_mesh.get_name()}")
        else:
            # Pick the first morph target to duplicate
            original_morph = morph_targets[0]
            original_name = original_morph.get_name()
            new_morph_name = "jawRight"  # Rename this morph

            # Duplicate by appending a reference

            morph_targets.append(original_morph)  # Append reference to the same morph
            morph_targets[-1].rename(new_morph_name)
            skeletal_mesh.set_editor_property("morph_targets", morph_targets)

            # Save the Skeletal Mesh
            ue.EditorAssetLibrary.save_asset(skeletal_mesh.get_path_name())

            # Log success
            ue.log(f"✅ Successfully duplicated morph '{original_name}' and renamed it to '{new_morph_name}' in '{skeletal_mesh.get_name()}'")
