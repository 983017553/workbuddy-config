"""
Template: parse yingmi MCP JSON outputs and generate a fund portfolio diagnosis HTML.
Copy and adapt for each report; file paths and holdings are placeholders.
"""
import json
from datetime import datetime


def parse_pct(s):
    if s is None:
        return 0
    s = str(s).replace('%', '')
    try:
        return float(s) / 100
    except Exception:
        return 0


# TODO: replace with actual user holdings
HOLDINGS = [
    {"code": "007339", "name": "易方达沪深300ETF联接C", "amount": 0},
    {"code": "000032", "name": "易方达信用债债券A", "amount": 0},
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_report(diagnosis, details, industries, correlation, output="report.html"):
    total = sum(h["amount"] for h in HOLDINGS)
    # ... build HTML using the yingmi demo-report.html shell ...
    with open(output, "w", encoding="utf-8") as f:
        f.write("<!-- report body -->")
    print(f"Report written to {output}")


if __name__ == "__main__":
    diag = load_json("diagnose-output.json")
    details = load_json("funds-detail.json")
    industries = load_json("industry-data.json")  # aggregated
    correlation = load_json("correlation.json")
    build_report(diag, details, industries, correlation)
