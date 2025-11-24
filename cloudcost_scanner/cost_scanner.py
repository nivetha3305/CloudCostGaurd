#!/usr/bin/env python3
"""
cost_scanner.py - improved CI-safe scanner.

Behavior:
 - Reads Terraform plan JSON (path via CLI arg or PLAN_PATH env or default ../costgaurd-infra/plan.json)
 - Loads budgets from budget.json (optional) or uses defaults
 - Uses pricing modules (same API you already have) to estimate costs
 - Writes cloudcost_scanner/output.json (or output.json in working dir)
 - DOES NOT launch Dash when running under CI (GITHUB_ACTIONS or CI env var)
 - When run locally (not CI) it will try to launch the dashboard if dash is available
"""

import os
import sys
import json
import argparse
import traceback

# optional: import dashboard only when needed
try:
    from dashboard import launch_dashboard
    DASH_AVAILABLE = True
except Exception:
    DASH_AVAILABLE = False

# your pricing modules (keep unchanged)
from pricing import (
    ec2_pricing,
    rds_pricing,
    s3_pricing,
    nat_pricing,
    eip_pricing,
    elb_pricing,
    others_pricing
)

# ----------------------
# Config / inputs
# ----------------------
DEFAULT_PLAN_PATHS = [
    os.path.join("..", "costgaurd-infra", "plan.json"),  # pipeline layout
    os.path.join("costgaurd-infra", "plan.json"),
    os.path.join("cloudcost_scanner", "plan.json"),
    "plan.json"
]
DEFAULT_OUTPUT = "output.json"
BUDGET_FILE = "budget.json"

# ----------------------
# Helpers
# ----------------------
def load_plan(path_candidates, override_path=None):
    if override_path:
        paths = [override_path]
    else:
        paths = path_candidates

    for p in paths:
        if os.path.exists(p):
            with open(p, "r") as f:
                return json.load(f), p
    return None, None

def load_budgets(budget_file):
    if os.path.exists(budget_file):
        try:
            with open(budget_file, "r") as bf:
                data = json.load(bf)
                print("📘 Loaded budgets from", budget_file)
                return data
        except Exception as e:
            print("⚠️ Failed to parse budget.json:", e)
    # default budgets
    print("⚙️ No valid budget.json found — using default budgets.")
    return {
        "aws_instance": 30.00,
        "aws_db_instance": 25.00,
        "aws_s3_bucket": 10.00,
        "aws_nat_gateway": 20.00,
        "aws_eip": 5.00,
        "aws_lb": 15.00,
        "aws_internet_gateway": 2.00,
        "overall_budget": 120.00
    }

def get_monthly_cost(res):
    res_type = res.get("type")
    try:
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
    except Exception as e:
        # price helpers may raise — return dict with note to keep scanner robust
        return {"monthly_cost": 0.0, "note": f"pricing-error: {str(e)}"}

def normalize_name(name):
    # shorten long names (optional), keep readable
    if not name:
        return "unknown"
    # remove repeating underscores and keep first two segments if long
    parts = name.split(".")
    if len(parts) > 2:
        return ".".join(parts[-2:])
    return name

# ----------------------
# Main scanner
# ----------------------
def main():
    parser = argparse.ArgumentParser(description="CloudCostGuard - Cost Scanner (CI-safe)")
    parser.add_argument("--plan", "-p", help="Path to terraform plan.json (overrides env and defaults)")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="Output JSON path")
    parser.add_argument("--no-dashboard", action="store_true", help="Do not launch dashboard even when running locally")
    args = parser.parse_args()

    plan_override = args.plan or os.environ.get("PLAN_PATH") or os.environ.get("TF_PLAN_PATH")
    plan_data, found_path = load_plan(DEFAULT_PLAN_PATHS, plan_override)
    if not plan_data:
        print("❌ No Terraform plan.json found. Searched:", DEFAULT_PLAN_PATHS, "and override:", plan_override)
        sys.exit(2)

    print("🔍 Using plan file:", found_path)

    # load budgets
    RESOURCE_BUDGET = load_budgets(BUDGET_FILE)

    # collect resources (including in child modules)
    resources = plan_data.get("planned_values", {}).get("root_module", {}).get("resources", [])
    child_modules = plan_data.get("planned_values", {}).get("root_module", {}).get("child_modules", []) or []
    for module in child_modules:
        resources.extend(module.get("resources", []))

    total_monthly_cost = 0.0
    resource_summary = []
    exceed_resources = []

    print("\nEstimating resource costs...\n")

    for res in resources:
        res_type = res.get("type")
        res_name = res.get("name")
        try:
            result = get_monthly_cost(res)
            if isinstance(result, dict):
                monthly_cost = float(result.get("monthly_cost", 0.0))
                note = result.get("note", "")
            else:
                monthly_cost = float(result)
                note = ""

            total_monthly_cost += monthly_cost

            budget = RESOURCE_BUDGET.get(res_type, RESOURCE_BUDGET.get("default_resource_budget", 9999.0))
            status = "✅ Within budget"
            if monthly_cost > budget:
                status = "🚨 Exceeded"
                exceed_resources.append(res_name)

            summary = {
                "name": normalize_name(res_name),
                "raw_name": res_name,
                "type": res_type,
                "estimated_cost": round(monthly_cost, 2),
                "budget": budget,
                "status": status,
                "note": note
            }
            resource_summary.append(summary)
            print(f"{res_type} ({summary['name']}): ${monthly_cost:.2f}/month  {status} {note}")

        except Exception as e:
            print(f"{res_type} ({res_name}): ❌ Error -> {e}")
            traceback.print_exc()
            continue

    overall_budget = RESOURCE_BUDGET.get("overall_budget", 0)
    print("\n------------------------------------------------")
    print(f"💰 Total Estimated Monthly Cost: ${total_monthly_cost:.2f}")
    print(f"🎯 Overall Budget: ${overall_budget:.2f}")
    print("------------------------------------------------")

    if total_monthly_cost > overall_budget:
        print("🚨 Total estimated cost exceeds overall budget limit!")
        exceed_resources.append("Total Budget")

    # prepare output
    output_data = {
        "resources": resource_summary,
        "total_estimated": round(total_monthly_cost, 2),
        "total_budget": overall_budget,
        "exceeded": bool(exceed_resources)
    }

    # write output file
    output_path = args.output
    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=4)
    print(f"\n✅ Wrote cost report to: {output_path}")

    # Print CLI summary for CI
    if exceed_resources:
        print(f"🚨 Budget exceeded for: {', '.join(sorted(set(exceed_resources)))}")
        print("🚫 Deployment halted (cost over budget).")
    else:
        print("✅ All resources within budget. Proceeding with deployment...")

    # Launch dashboard only when NOT running in CI and user allows it
    running_in_ci = os.environ.get("GITHUB_ACTIONS") == "true" or os.environ.get("CI") == "true"
    want_dashboard = (not running_in_ci) and (not args.no_dashboard) and DASH_AVAILABLE

    if want_dashboard:
        try:
            print("\n📊 Launching cost dashboard...")
            dashboard_link = launch_dashboard(output_path)
            print(f"🔗 Dashboard running at: {dashboard_link}")
            print("Press CTRL+C to stop the dashboard server.")
            # keep process alive only when launching dashboard locally
            # launch_dashboard is expected to block/run server; if not, block here:
            try:
                while True:
                    pass
            except KeyboardInterrupt:
                print("Stopping dashboard...")
        except Exception as e:
            print("⚠️ Failed to launch dashboard:", e)
    else:
        if running_in_ci:
            print("ℹ️ Running in CI — dashboard disabled. Download the output.json artifact and run the dashboard locally.")
        elif not DASH_AVAILABLE:
            print("ℹ️ Dashboard module not available locally. Install dash and run dashboard.py if you want a local UI.")
        else:
            print("ℹ️ Dashboard launch skipped (use --no-dashboard to force skip).")

    # exit status: non-zero when exceeded OR error (we used earlier codes)
    if exceed_resources:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
