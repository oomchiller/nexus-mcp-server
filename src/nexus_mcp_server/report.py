from typing import Any, Dict, List

def to_markdown_table(data: List[Dict[str, Any]], columns: List[str]) -> str:
    """Convert a list of dicts to a markdown table."""
    if not data:
        return "No data available."

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for item in data:
        row = "| " + " | ".join([str(item.get(col, "")) for col in columns]) + " |"
        rows.append(row)

    return "\n".join([header, separator] + rows)

def generate_report_header(title: str, nexus_url: str) -> str:
    return f"# {title}\n\n**Instance:** {nexus_url}\n\n"
