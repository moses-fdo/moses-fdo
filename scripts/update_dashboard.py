import urllib.request
import json
import re
import datetime
import os
from html.parser import HTMLParser

# ==============================================================================
# 1. CONTRIBUTION HEATMAP ENGINE
# ==============================================================================

class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {} # maps (row, col) -> {level: int, date: str}
        
    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            d = dict(attrs)
            if 'id' in d and d['id'].startswith('contribution-day-component-'):
                match = re.match(r'contribution-day-component-(\d+)-(\d+)', d['id'])
                if match:
                    row, col = int(match.group(1)), int(match.group(2))
                    lvl = int(d.get('data-level', 0))
                    date = d.get('data-date', '')
                    self.cells[(row, col)] = {'level': lvl, 'date': date}

def fetch_contributions():
    url = 'https://github.com/users/moses-fdo/contributions'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

def generate_heatmap_svg(cells):
    colors = {
        0: "#1b1b1f",  # Level 0 (bg charcoal)
        1: "#4b4b54",  # Level 1
        2: "#82828c",  # Level 2
        3: "#c0c0c8",  # Level 3
        4: "#ffffff"   # Level 4 (white)
    }

    svg_content = []
    svg_content.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 152" width="100%" height="auto">')
    svg_content.append('  <defs>')
    svg_content.append('    <style>')
    svg_content.append('      @import url(\'https://fonts.googleapis.com/css2?family=JetBrains+Mono\');')
    svg_content.append('      :root {')
    svg_content.append('        --bg-color: #0f0f11;')
    svg_content.append('        --card-bg: #0d0d0f;')
    svg_content.append('        --border-color: rgba(255, 255, 255, 0.08);')
    svg_content.append('        --text-color: #a1a1aa;')
    svg_content.append('      }')
    svg_content.append('      @media (prefers-color-scheme: light) {')
    svg_content.append('        :root {')
    svg_content.append('          --bg-color: #f8fafc;')
    svg_content.append('          --card-bg: #ffffff;')
    svg_content.append('          --border-color: rgba(0, 0, 0, 0.08);')
    svg_content.append('          --text-color: #64748b;')
    svg_content.append('        }')
    svg_content.append('      }')
    svg_content.append('      .bg { fill: none; }')
    svg_content.append('      .card { fill: var(--card-bg); stroke: none; }')
    svg_content.append('      .lbl { font-family: \'JetBrains Mono\', monospace; font-size: 9px; fill: var(--text-color); }')
    svg_content.append('    </style>')
    svg_content.append('  </defs>')
    
    # Background & Frame
    svg_content.append('  <rect width="900" height="152" class="bg" />')
    svg_content.append('  <rect x="0" y="0" width="900" height="152" rx="8" class="card" />')
    
    # Compute Month Labels dynamically based on date objects in column 0-52
    month_labels = []
    prev_month = None
    for col in range(53):
        col_cells = [cells[(r, col)] for r in range(7) if (r, col) in cells]
        if not col_cells:
            continue
        col_cells.sort(key=lambda x: x['date'])
        try:
            dt = datetime.datetime.strptime(col_cells[0]['date'], "%Y-%m-%d")
            month_name = dt.strftime("%b")
            if month_name != prev_month:
                if not month_labels or (col - month_labels[-1][1]) >= 2:
                    month_labels.append((month_name, col))
                    prev_month = month_name
        except Exception:
            pass

    # Draw Month Labels
    for name, col_idx in month_labels:
        x_pos = 50 + col_idx * 14
        svg_content.append(f'  <text x="{x_pos}" y="24" class="lbl">{name}</text>')
        
    # Day Labels
    days = [("Mon", 1), ("Wed", 3), ("Fri", 5)]
    for name, row_idx in days:
        y_pos = 34 + row_idx * 14 + 8
        svg_content.append(f'  <text x="25" y="{y_pos}" class="lbl">{name}</text>')
        
    # Render Cells
    start_x = 50
    start_y = 29
    
    for col in range(53):
        x = start_x + col * 14
        for row in range(7):
            y = start_y + row * 14
            cell_data = cells.get((row, col), {'level': 0, 'date': ''})
            lvl = cell_data['level']
            color = colors.get(lvl, colors[0])
            svg_content.append(f'  <rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{color}" />')
                
    # Legend
    legend_start_x = 730
    legend_y = 131
    svg_content.append(f'  <text x="{legend_start_x - 30}" y="{legend_y + 8}" class="lbl">Less</text>')
    for l in range(5):
        lx = legend_start_x + l * 14
        color = colors[l]
        svg_content.append(f'  <rect x="{lx}" y="{legend_y}" width="10" height="10" rx="2" fill="{color}" />')
    svg_content.append(f'  <text x="{legend_start_x + 5 * 14 + 5}" y="{legend_y + 8}" class="lbl">More</text>')

    svg_content.append('</svg>')
    return "\n".join(svg_content)


# ==============================================================================
# 2. STATS ENGINE
# ==============================================================================

def fetch_json(url, token=None):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    if token:
        req.add_header('Authorization', f'token {token}')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_stats(username, token=None):
    # 1. Total Stars
    repos = fetch_json(f"https://api.github.com/users/{username}/repos?per_page=100", token)
    stars = sum(repo.get('stargazers_count', 0) for repo in repos) if repos else 0
    
    # 2. Total Commits
    commits_data = fetch_json(f"https://api.github.com/search/commits?q=author:{username}", token)
    commits = commits_data.get('total_count', 0) if commits_data else 0
    
    # 3. Total PRs
    prs_data = fetch_json(f"https://api.github.com/search/issues?q=author:{username}+type:pr", token)
    prs = prs_data.get('total_count', 0) if prs_data else 0
    
    # 4. Total Issues
    issues_data = fetch_json(f"https://api.github.com/search/issues?q=author:{username}+type:issue", token)
    issues = issues_data.get('total_count', 0) if issues_data else 0
    
    return {
        'stars': stars,
        'commits': commits,
        'prs': prs,
        'issues': issues
    }

def generate_stats_svg(stats):
    stars = stats['stars']
    commits = stats['commits']
    prs = stats['prs']
    issues = stats['issues']
    
    # Compute rank/score
    score = commits * 2 + prs * 4 + stars * 10 + issues
    if score > 200:
        grade = "A+"
        percent = 95
    elif score > 100:
        grade = "A"
        percent = 80
    elif score > 50:
        grade = "B+"
        percent = 65
    else:
        grade = "B"
        percent = 50
        
    # Circumference of r=40 is 251.2
    dashoffset = 251.2 - (251.2 * percent / 100)
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 495 195" width="495" height="195">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono');
      :root {{
        --bg-color: #0d0d0f;
        --accent-glow: #ffffff;
        --text-main: #ffffff;
        --text-muted: #a1a1aa;
        --text-dark: #767680;
        --border-color: #2a2a30;
      }}
      @media (prefers-color-scheme: light) {{
        :root {{
          --bg-color: #ffffff;
          --accent-glow: #0969da;
          --text-main: #0f172a;
          --text-muted: #64748b;
          --text-dark: #94a3b8;
          --border-color: #e5e7eb;
        }}
      }}
      .jb-mono {{ font-family: 'JetBrains Mono', monospace; }}
      .card {{ fill: var(--bg-color); stroke: none; }}
      
      @keyframes smoothFadeIn {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
      }}
      .anim-line-1 {{ animation: smoothFadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; animation-delay: 0.2s; opacity: 0; }}
      .anim-line-2 {{ animation: smoothFadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; animation-delay: 0.4s; opacity: 0; }}
      .anim-line-3 {{ animation: smoothFadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; animation-delay: 0.6s; opacity: 0; }}
      .anim-line-4 {{ animation: smoothFadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards; animation-delay: 0.8s; opacity: 0; }}
    </style>
  </defs>

  <rect x="0.5" y="0.5" width="494" height="194" rx="8" class="card" />

  <text x="25" y="32" class="jb-mono" font-size="9" font-weight="700" fill="var(--text-dark)" letter-spacing="2">GITHUB STATS</text>

  <!-- Stats List -->
  <g transform="translate(25, 65)" class="jb-mono" font-size="11" fill="var(--text-muted)">
    <text x="0" y="0" class="anim-line-1" fill="var(--text-main)" font-weight="700">Total Stars: <tspan fill="var(--accent-glow)">{stars}</tspan></text>
    <text x="0" y="24" class="anim-line-2">Total Commits: <tspan fill="var(--text-main)">{commits}</tspan></text>
    <text x="0" y="48" class="anim-line-3">Total PRs: <tspan fill="var(--text-main)">{prs}</tspan></text>
    <text x="0" y="72" class="anim-line-4">Total Issues: <tspan fill="var(--text-main)">{issues}</tspan></text>
  </g>

  <!-- Grade Ring Indicator -->
  <g transform="translate(380, 105)" class="jb-mono">
    <circle cx="0" cy="0" r="40" fill="none" stroke="var(--text-dark)" stroke-opacity="0.2" stroke-width="6" />
    <circle cx="0" cy="0" r="40" fill="none" stroke="var(--accent-glow)" stroke-width="6" stroke-dasharray="251.2" stroke-dashoffset="{dashoffset}" transform="rotate(-90)" stroke-linecap="round" />
    <text x="0" y="8" font-size="20" font-weight="700" fill="var(--text-main)" text-anchor="middle">{grade}</text>
  </g>
</svg>"""
    return svg


# ==============================================================================
# 3. UNIFIED EXECUTION MAIN
# ==============================================================================

def main():
    assets_dir = '/home/mosesfdo/Documents/GitHub/moses-fdo/assets'
    os.makedirs(assets_dir, exist_ok=True)
    
    # Run Heatmap Component
    try:
        html = fetch_contributions()
        parser = ContributionParser()
        parser.feed(html)
        if parser.cells:
            svg = generate_heatmap_svg(parser.cells)
            with open(os.path.join(assets_dir, 'heatmap.svg'), 'w') as f:
                f.write(svg)
            print("Successfully updated real-time contribution heatmap.")
        else:
            print("Warning: Heatmap HTML parser parsed 0 cells.")
    except Exception as e:
        print(f"Error updating contribution heatmap: {e}")

    # Run Stats Component
    try:
        token = os.environ.get('GITHUB_TOKEN')
        stats = get_stats('moses-fdo', token)
        if stats:
            svg = generate_stats_svg(stats)
            with open(os.path.join(assets_dir, 'stats-card.svg'), 'w') as f:
                f.write(svg)
            print("Successfully generated custom stats card.")
        else:
            print("Warning: Stats API fetched empty stats.")
    except Exception as e:
        print(f"Error updating stats card: {e}")

if __name__ == '__main__':
    main()
