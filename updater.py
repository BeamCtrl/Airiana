#!/usr/bin/python3
import os
import sys
import pickle
import json

path = os.path.abspath(__file__).replace("updater.py", "")
os.chdir(path)


def migrate_coef_to_json():
    """Automatically migrate coeficients.dat to JSON if found."""
    pickle_file = "coeficients.dat"
    json_file = "coeficients.json"
    
    if not os.path.isfile(pickle_file):
        return
    
    # If JSON already exists, just delete the old pickle file
    if os.path.isfile(json_file):
        print(f"[Migration] {json_file} exists. Removing old {pickle_file}...")
        os.remove(pickle_file)
        return
    
    try:
        print(f"[Migration] Found {pickle_file}. Converting to JSON...")
        with open(pickle_file, "rb") as f:
            coef_dict = pickle.load(f)
        
        # Convert to JSON format
        data = {str(k): {str(dk): dv for dk, dv in v.items()} for k, v in coef_dict.items()}
        
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[Migration] ✓ Successfully converted to {json_file}")
        
        # Remove old pickle file
        os.remove(pickle_file)
        print(f"[Migration] ✓ Removed {pickle_file}")
        
    except Exception as e:
        print(f"[Migration] ✗ Error migrating coefficients: {e}")


def main():
    """Main updater function."""
    deb_versions = ("wheezy", "jessie", "stretch", "buster", "bullseye", "bookworm")

    for system in enumerate(deb_versions):
        os_name = os.popen("./osname.py").readline()[:-1]
        if os_name in system and deb_versions.index(os_name) <= len(deb_versions) - 3:
            print("current", system[1])
            print("future", deb_versions[system[0] + 1])
            # print("Updating to", deb_versions[system[0]+1])
            # print("./systemfiles/upgrade.sh " + system[1] + " " + deb_versions[system[0] + 1])
            # os.system("./systemfiles/upgrade.sh " + system[1] + " " + deb_versions[system[0]+1]  + " >> update.log")
            # os.system("python3 install.py clean headless")
            # os.system("python3 install.py update headless")
            # os.system("sudo reboot")
            break

    os.system("git fetch && git checkout -m origin/master ./public/current_version")
    ver = os.popen("cat ./public/current_version").read()
    ver = ver.split(" ")
    tmp = os.popen("head -30 airiana-core.py").readlines()
    for each in tmp:
        if "vers" in each:
            temp = each.split("=")
            vers = temp[-1][2:-2]

    # Run migration json migration after updating.
    migrate_coef_to_json()

    if "debug" in sys.argv:
        print(vers, "->", ver, "will update", vers not in ver[0])
    if vers not in ver[0] and "Valid" in ver[1]:
        print("Updating Airiana system software to", ver[0])
        if "debug" not in sys.argv or len(sys.argv) > 1:
            os.system("./update")
            # os.system("python3 install.py clean headless")
            # os.system("python3 install.py update headless")


if __name__ == "__main__":
    main()
