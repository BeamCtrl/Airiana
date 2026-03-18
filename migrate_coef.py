#!/usr/bin/env python3
"""
Migration script: Convert coeficients.dat (pickle) to coeficients.json
"""
import pickle
import json
import os
import sys


def migrate_coef():
    pickle_file = "coeficients.dat"
    json_file = "coeficients.json"
    
    # Check if pickle file exists
    if not os.path.isfile(pickle_file):
        print(f"✗ {pickle_file} not found. Nothing to migrate.")
        sys.exit(1)
    
    # Check if JSON already exists
    if os.path.isfile(json_file):
        print(f"✗ {json_file} already exists. Backup or remove the old JSON file first.")
        sys.exit(1)
    
    try:
        # Load pickle file
        print(f"Reading {pickle_file}...")
        with open(pickle_file, "rb") as f:
            coef_dict = pickle.load(f)
        
        print(f"Loaded data: {coef_dict}")
        
        # Convert to JSON format (int keys -> str keys for JSON)
        data = {str(k): {str(dk): dv for dk, dv in v.items()} for k, v in coef_dict.items()}
        
        # Write to JSON
        print(f"Writing to {json_file}...")
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Migration complete!")
        print(f"✓ {json_file} created successfully")
        print(f"\nBackup of original file recommended before deletion:")
        print(f"  cp {pickle_file} {pickle_file}.backup")
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    migrate_coef()
