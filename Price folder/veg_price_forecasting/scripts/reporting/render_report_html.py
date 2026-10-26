from pathlib import Path
import markdown

md_path = Path("results/report.md")
html_path = Path("results/report.html")

md_content = md_path.read_text(encoding="utf-8")
body_html = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Sri Lankan Market Vegetable Price Forecasting - Research Report</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      max-width: 960px;
      margin: 40px auto;
      padding: 0 24px;
      line-height: 1.65;
      color: #24292e;
      background-color: #ffffff;
    }}
    h1, h2, h3, h4 {{
      color: #1a202c;
      border-bottom: 1px solid #eaecef;
      padding-bottom: 0.3em;
      margin-top: 1.5em;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 24px 0;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid #dfe2e5;
      padding: 10px 14px;
      text-align: left;
    }}
    th {{
      background-color: #f6f8fa;
      font-weight: 600;
    }}
    tr:nth-child(2n) {{
      background-color: #fcfcfc;
    }}
    code {{
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
      background-color: #f3f4f6;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 85%;
    }}
    pre {{
      background-color: #f6f8fa;
      border-radius: 6px;
      padding: 16px;
      overflow: auto;
      font-size: 85%;
      line-height: 1.45;
    }}
    blockquote {{
      margin: 0;
      padding: 0 1em;
      color: #6a737d;
      border-left: 0.25em solid #dfe2e5;
    }}
    ol, ul {{
      padding-left: 2em;
    }}
    li {{
      margin-bottom: 0.5em;
    }}
  </style>
</head>
<body>
{body_html}
</body>
</html>
"""

html_path.write_text(full_html, encoding="utf-8")
print(f"Generated {html_path} ({len(full_html)} bytes)")
