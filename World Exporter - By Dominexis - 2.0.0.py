# Import libraries

import os
import shutil
import random
import json
from pathlib import Path
import sys



# Check that correct Python version is running

if not (
    (sys.version_info[0] == 3 and sys.version_info[1] >= 9)
    or
    (sys.version_info[0] > 3)
):
    print("\n\n ERROR: World Exporter requires Python 3.9 or newer!")
    input()
    exit()



# Initialize variables

PROGRAM_PATH = Path(__file__).parent
print("\n\n World Exporter - By Dominexis - 2.0.0")
print("\n Leave world name blank to exit.")
print(" Leave add-on input blank to not install another add-on.")
print(" Drag .mcaddon files onto the terminal when prompted to enter add-ons to install.")
random.seed()






# Define functions

def program():
    while True:
        # Get world name
        world_name = input("\n World name: ")
        if world_name == "":
            exit()

        # Get list of add-ons
        addon_list: list[str] = []
        while True:
            addon_path = input(" Add-on to install: ")
            if addon_path == "":
                break
            if addon_path in addon_list:
                print(" ERROR: Add-on already listed!")
                continue
            addon_list.append(addon_path)

        # Find world
        world_folder = find_world(world_name)
        if world_folder == "":
            continue

        # Remove existing copy of world
        if (PROGRAM_PATH / "World Exports" / world_name).exists():
            shutil.rmtree(PROGRAM_PATH / "World Exports" / world_name)

        # Copy world
        shutil.copytree(
            PROGRAM_PATH / "minecraftWorlds" / world_folder,
            PROGRAM_PATH / "World Exports" / world_name
        )

        # Extract UUIDs of packs
        bp_uuids = get_installed_pack_uuids(world_name, "behavior")
        rp_uuids = get_installed_pack_uuids(world_name, "resource")

        # Find packs based on UUID
        find_packs_from_uuid(world_name, bp_uuids, "behavior")
        find_packs_from_uuid(world_name, rp_uuids, "resource")



        # Import add-ons to world
        temp_folder = PROGRAM_PATH / "temp_pack_folder"
        for addon in addon_list:
            if not Path(addon).exists():
                print(f' ERROR: Add-on "{Path(addon).name}" not found!')
                continue

            # Unzip archive
            if temp_folder.exists():
                shutil.rmtree(temp_folder)
            shutil.unpack_archive(Path(addon), temp_folder, "zip")

            # Iterate through packs
            for pack_path in temp_folder.iterdir():
                if not (pack_path / "manifest.json").exists():
                    continue
                pack_uuid, pack_type = import_pack(PROGRAM_PATH / "World Exports" / world_name, pack_path)
                if pack_type == "behavior":
                    bp_uuids.append(pack_uuid)
                if pack_type == "resource":
                    rp_uuids.append(pack_uuid)

        if temp_folder.exists():
            shutil.rmtree(temp_folder)



        # Generate list of random UUIDs
        new_bp_uuids: list[str] = []
        new_rp_uuids: list[str] = []
        for uuid in bp_uuids:
            new_bp_uuids.append(random_uuid())
        for uuid in rp_uuids:
            new_rp_uuids.append(random_uuid())

        # Change UUID references
        pack_replace_uuid(PROGRAM_PATH / "World Exports" / world_name / "behavior_packs", bp_uuids, new_bp_uuids)
        pack_replace_uuid(PROGRAM_PATH / "World Exports" / world_name / "resource_packs", rp_uuids, new_rp_uuids)
        replace_uuid(PROGRAM_PATH / "World Exports" / world_name / "world_behavior_packs.json"       , bp_uuids, new_bp_uuids)
        replace_uuid(PROGRAM_PATH / "World Exports" / world_name / "world_behavior_pack_history.json", bp_uuids, new_bp_uuids)
        replace_uuid(PROGRAM_PATH / "World Exports" / world_name / "world_resource_packs.json"       , rp_uuids, new_rp_uuids)
        replace_uuid(PROGRAM_PATH / "World Exports" / world_name / "world_resource_pack_history.json", rp_uuids, new_rp_uuids)

        # Zip world
        if (PROGRAM_PATH / "World Exports" / f"{world_name}.mcworld").exists():
            os.remove(PROGRAM_PATH / "World Exports" / f"{world_name}.mcworld")
        shutil.make_archive(
            PROGRAM_PATH / "World Exports" / world_name,
            "zip",
            PROGRAM_PATH / "World Exports" / world_name
        )
        os.rename(
            PROGRAM_PATH / "World Exports" / f"{world_name}.zip",
            PROGRAM_PATH / "World Exports" / f"{world_name}.mcworld"
        )

        # Remove old directory
        shutil.rmtree(PROGRAM_PATH / "World Exports" / world_name)

        print(" World successfully exported.")



def find_world(world_name: str) -> str:
    for path in (PROGRAM_PATH / "minecraftWorlds").iterdir():
        # Skip if the level name file doesn't exist
        if not (path / "levelname.txt").exists():
            continue

        # Extract name of world
        with (path / "levelname.txt").open("r", encoding="utf-8") as file:
            name = file.read().replace("\n", "")

        # Exit loop if world is found
        if name == world_name:
            return path.name

    print(f' ERROR: World "{world_name}" not found!')
    return ""

def get_installed_pack_uuids(world_name: str, pack_type: str) -> list[str]:
    uuids: list[str] = []
    if (PROGRAM_PATH / "World Exports" / world_name / f"world_{pack_type}_packs.json").exists():
        with (PROGRAM_PATH / "World Exports" / world_name / f"world_{pack_type}_packs.json").open("r", encoding="utf-8") as file:
            uuid_file: dict = json.load(file)
        for entry in uuid_file:
            uuids.append(entry["pack_id"])
    return uuids



def find_packs_from_uuid(world_name: str, uuids: list[str], pack_type: str):
    # Find packs based on UUID
    for uuid in uuids:
        # Existing packs
        if find_packs_from_source(
            PROGRAM_PATH / "World Exports" / world_name / f"{pack_type}_packs",
            PROGRAM_PATH / "World Exports" / world_name / f"{pack_type}_packs",
            uuid
        ):
            return

        # Stored packs
        if find_packs_from_source(
            PROGRAM_PATH / f"{pack_type}_packs",
            PROGRAM_PATH / "World Exports" / world_name / f"{pack_type}_packs",
            uuid
        ):
            return

        # Development packs
        if find_packs_from_source(
            PROGRAM_PATH / f"development_{pack_type}_packs",
            PROGRAM_PATH / "World Exports" / world_name / f"{pack_type}_packs",
            uuid
        ):
            return

def find_packs_from_source(source_path: Path, world_path: Path, pack_uuid: str):
    # Cancel if the source folder doesn't exist
    if not source_path.exists():
        return False

    # Iterate through packs
    for pack_path in source_path.iterdir():

        # Skip if manifest.json doesn't exist
        if not (pack_path / "manifest.json").exists():
            continue

        # Extract UUID from pack and compare it
        with (pack_path / "manifest.json").open("r", encoding="utf-8") as file:
            uuid: str = json.load(file)["header"]["uuid"]
        if pack_uuid == uuid:
            if source_path != world_path:
                shutil.copytree(
                    pack_path,
                    world_path / pack_path.name
                )
            return True

    return False



def import_pack(world_path: Path, pack_path: Path) -> tuple[str, str]:
    # Determine if pack is a resource pack or a behavior pack
    with (pack_path / "manifest.json").open("r", encoding="utf-8") as file:
        contents = json.load(file)

    pack_type: str = contents["modules"][0]["type"]
    pack_name: str = contents["header"]["name"]
    pack_uuid: str = contents["header"]["uuid"]
    pack_version: list[int] = contents["header"]["version"]

    if pack_type in ["data", "client_data", "javascript", "world_template", "interface"]:
        pack_type = "behavior"
    else:
        pack_type = "resource"

    # Import pack into world
    shutil.copytree(
        pack_path,
        world_path / f'{pack_type}_packs' / pack_path.name
    )
    insert_uuid(world_path / f'world_{pack_type}_packs.json',        True,  pack_name, pack_uuid, pack_version)
    insert_uuid(world_path / f'world_{pack_type}_pack_history.json', False, pack_name, pack_uuid, pack_version)

    return pack_uuid, pack_type

def insert_uuid(file_path: Path, normal: bool, pack_name: str, pack_uuid: str, pack_version: list[int]):
    with file_path.open("r", encoding="utf-8") as file:
        contents: list[dict] | dict[str, list[dict]] = json.load(file)

    # Add pack to contents
    if normal:
        contents.append(
            {
                "pack_id": pack_uuid,
                "version": pack_version
            }
        )
    else:
        contents["packs"].append(
            {
                "can_be_redownloaded": False,
                "name": pack_name,
                "uuid": pack_uuid,
                "version": pack_version
            }
        )

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(contents, file)



HEX_CHARS = ["0","1","2","3","4","5","6","7","8","9","a","b","c","d","e","f"]
def random_uuid() -> str:
    uuid = ""
    for i in range(32):
        uuid += random.choice(HEX_CHARS)
    return uuid[0:8] + "-" + uuid[8:12] + "-" + uuid[12:16] + "-" + uuid[16:20] + "-" + uuid[20:32]

def replace_uuid(path: Path, uuids: list[str], new_uuids: list[str]):
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as file:
        contents = file.read()
    for index in range(len(uuids)):
        contents = contents.replace(uuids[index], new_uuids[index])
    with path.open("w", encoding="utf-8") as file:
        file.write(contents)

def pack_replace_uuid(path: Path, uuids: list[str], new_uuids: list[str]):
    if not path.exists():
        return
    for path in path.iterdir():
        if not (path / "manifest.json").exists():
            continue
        replace_uuid(path / "manifest.json", uuids, new_uuids)





    

# Run program

program()