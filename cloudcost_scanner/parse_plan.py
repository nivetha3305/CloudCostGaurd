import json
import os

# --- Step 1: Locate plan.json ---
# Adjust this path if needed (assuming your plan.json is in cost_infra folder)
PLAN_PATH = os.path.join("..", "costgaurd-infra", "plan.json")

# --- Step 2: Load JSON file ---
with open(PLAN_PATH, "r") as file:
    plan_data = json.load(file)

# --- Step 3: Extract resources ---
resources = plan_data.get("planned_values", {}).get("root_module", {}).get("resources", [])
child_modules = plan_data.get("planned_values", {}).get("root_module", {}).get("child_modules", [])

# Include resources inside nested modules (if any)
for module in child_modules:
    resources.extend(module.get("resources", []))

# --- Step 4: Display all resource types ---
print("Detected resources in Terraform plan:\n")
for res in resources:
    res_type = res.get("type")
    res_name = res.get("name")
    res_values = res.get("values", {})
    print(f"Resource: {res_type}.{res_name}")

    # Try to print common attributes
    for key in ["instance_type", "region", "size", "bucket", "allocated_storage"]:
        if key in res_values:
            print(f"  {key}: {res_values[key]}")

    print("-" * 50)

print(f"\n✅ Total resources found: {len(resources)}")
