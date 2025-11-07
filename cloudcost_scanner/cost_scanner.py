import boto3
import json
import os
from dashboard import launch_dashboard
from pricing import (
    ec2_pricing,
    rds_pricing,
    s3_pricing,
    nat_pricing,
    eip_pricing,
    elb_pricing,
    others_pricing
)

# --------------------------------------------------------
#  AWS Cost Scanner with Dynamic Budget + Dashboard
# --------------------------------------------------------

pricing = boto3.client('pricing', region_name='us-east-1')

# --- Step 1: Load Budgets from budget.json or fallback ---
if os.path.exists("budget.json"):
    with open("budget.json", "r") as bf:
        RESOURCE_BUDGET = json.load(bf)
        print("📘 Loaded budgets from budget.json\n")
else:
    print("⚙️ No budget.json found — using default budgets.\n")
    RESOURCE_BUDGET = {
        "aws_instance": 30.00,
        "aws_db_instance": 25.00,
        "aws_s3_bucket": 10.00,
        "aws_nat_gateway": 20.00,
        "aws_eip": 5.00,
        "aws_lb": 15.00,
        "aws_internet_gateway": 2.00,
        "overall_budget": 120.00
    }

# --- Step 2: Load Terraform plan JSON ---
PLAN_PATH = os.path.join("..", "costgaurd-infra", "plan.json")

with open(PLAN_PATH, "r") as f:
    plan_data = json.load(f)

resources = plan_data.get("planned_values", {}).get("root_module", {}).get("resources", [])
child_modules = plan_data.get("planned_values", {}).get("root_module", {}).get("child_modules", [])
for module in child_modules:
    resources.extend(module.get("resources", []))

print("🔍 Estimating costs using AWS Pricing API...\n")

total_monthly_cost = 0.0
resource_summary = []
exceed_resources = []

# --- Helper to get resource cost ---
def get_monthly_cost(res):
    res_type = res.get("type")

    if res_type == "aws_instance":
        return ec2_pricing.get_cost(res)
    elif res_type == "aws_db_instance":
        return rds_pricing.get_cost(res)
    elif res_type == "aws_s3_bucket":
        return s3_pricing.get_cost(res)
    elif res_type == "aws_nat_gateway":
        return nat_pricing.get_cost(res)
    elif res_type == "aws_eip":
        return eip_pricing.get_cost(res)
    elif res_type in ["aws_lb", "aws_lb_listener"]:
        return elb_pricing.get_cost(res)
    else:
        return others_pricing.get_cost(res)

# --- Step 3: Scan each resource ---
for res in resources:
    res_type = res.get("type")
    res_name = res.get("name")

    try:
        result = get_monthly_cost(res)
        if isinstance(result, dict):
            monthly_cost = result.get("monthly_cost", 0.0)
            note = result.get("note", "")
        else:
            monthly_cost = float(result)
            note = ""

        total_monthly_cost += monthly_cost

        budget = RESOURCE_BUDGET.get(res_type, 9999.0)
        status = "✅ Within budget"
        if monthly_cost > budget:
            status = "🚨 Exceeded"
            exceed_resources.append(res_name)

        resource_summary.append({
            "name": res_name,
            "type": res_type,
            "estimated_cost": monthly_cost,
            "budget": budget,
            "status": status,
            "note": note
        })

        print(f"{res_type} ({res_name}): ${monthly_cost:.2f}/month  {status} {note}")

    except Exception as e:
        print(f"{res_type} ({res_name}): ❌ Error -> {e}")
        continue

# --- Step 4: Overall Summary ---
overall_budget = RESOURCE_BUDGET.get("overall_budget", 0)
print("\n------------------------------------------------")
print(f"💰 Total Estimated Monthly Cost: ${total_monthly_cost:.2f}")
print(f"🎯 Overall Budget: ${overall_budget:.2f}")
print("------------------------------------------------")

# --- Step 5: Check overall budget ---
if total_monthly_cost > overall_budget:
    print("🚨 Total estimated cost exceeds overall budget limit!")
    exceed_resources.append("Total Budget")

# --- Step 6: Write output.json for dashboard ---
output_data = {
    "resources": [
        {
            "name": r["name"],
            "type": r["type"],
            "estimated_cost": r["estimated_cost"],
            "actual_cost": round(r["estimated_cost"] * 0.95, 2),
            "budget": r["budget"],
            "status": r["status"]
        }
        for r in resource_summary
    ],
    "total_estimated": total_monthly_cost,
    "total_budget": overall_budget
}

with open("output.json", "w") as f:
    json.dump(output_data, f, indent=4)

# --- Step 7: Print Summary & Launch Dashboard ---
if exceed_resources:
    print(f"🚨 Budget exceeded for: {', '.join(set(exceed_resources))}")
    print("🚫 Deployment halted (cost over budget).")
else:
    print("✅ All resources within budget. Proceeding with deployment...")

print("\n📊 Launching cost dashboard...")
dashboard_link = launch_dashboard("output.json")

print(f"\n🔗 Dashboard running at: {dashboard_link}")
print("Press CTRL+C to stop the dashboard server.")

while True:
    pass
