import json
import os
import urllib.request
from datetime import datetime, timezone

query = '''query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
    }
  }
}'''
request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": query, "variables": {"login": os.environ["GITHUB_ACTOR"]}}).encode(),
    headers={
        "Authorization": f"Bearer {os.environ['GH_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "activity-radar-updater",
    },
)
with urllib.request.urlopen(request) as response:
    payload = json.load(response)
if payload.get("errors"):
    raise SystemExit(json.dumps(payload["errors"]))

contributions = payload["data"]["user"]["contributionsCollection"]
values = {
    "Commits": contributions["totalCommitContributions"],
    "Issues": contributions["totalIssueContributions"],
    "Pull requests": contributions["totalPullRequestContributions"],
    "Code reviews": contributions["totalPullRequestReviewContributions"],
}
maximum = max(values.values(), default=1) or 1
center_x, center_y, radius = 280, 270, 160
angles = [-90, 0, 90, 180]
points = []
for angle, value in zip(angles, values.values()):
    import math
    distance = radius * value / maximum
    radians = math.radians(angle)
    points.append((center_x + distance * math.cos(radians), center_y + distance * math.sin(radians)))
polygon = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
labels = [
    (center_x, center_y - radius - 20, "middle", "Commits"),
    (center_x + radius + 24, center_y + 6, "start", "Issues"),
    (center_x, center_y + radius + 28, "middle", "Pull requests"),
    (center_x - radius - 24, center_y + 6, "end", "Code reviews"),
]
label_svg = "".join(
    f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="#8b949e" font-family="Arial,sans-serif" font-size="16">{text}</text>'
    for x, y, anchor, text in labels
)
value_svg = "".join(
    f'<text x="{x}" y="{y}" text-anchor="middle" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="14">{value}</text>'
    for (x, y), value in zip(points, values.values())
)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="720" height="500" viewBox="0 0 720 500">
<rect width="720" height="500" rx="18" fill="#0d1117"/>
<text x="360" y="42" text-anchor="middle" fill="#f0f6fc" font-family="Arial,sans-serif" font-size="24" font-weight="700">GitHub Activity Radar</text>
<g>
<polygon points="280,110 440,270 280,430 120,270" fill="none" stroke="#30363d"/>
<polygon points="280,190 360,270 280,350 200,270" fill="none" stroke="#30363d"/>
<line x1="280" y1="110" x2="280" y2="430" stroke="#30363d"/><line x1="120" y1="270" x2="440" y2="270" stroke="#30363d"/>
<polygon points="{polygon}" fill="#2ea043" fill-opacity=".35" stroke="#3fb950" stroke-width="3"/>
{value_svg}
{label_svg}
</g>
<text x="360" y="472" text-anchor="middle" fill="#8b949e" font-family="Arial,sans-serif" font-size="13">Updated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} · Scaled to the highest category</text>
</svg>
'''
with open("assets/activity-radar.svg", "w", encoding="utf-8") as file:
    file.write(svg)
