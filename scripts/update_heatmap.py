import urllib.request
import re
import datetime
import os
from html.parser import HTMLParser

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

def generate_svg(cells):
    # Charcoal theme color palette
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
        # Gather dates in this column
        col_cells = [cells[(r, col)] for r in range(7) if (r, col) in cells]
        if not col_cells:
            continue
        col_cells.sort(key=lambda x: x['date'])
        # Parse the month
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
        y_pos = 34 + row_idx * 14 + 8 # align nicely
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

def main():
    try:
        html = fetch_contributions()
        parser = ContributionParser()
        parser.feed(html)
        
        if not parser.cells:
            raise ValueError("No cells were parsed. Check GitHub response or selectors.")
            
        svg = generate_svg(parser.cells)
        
        # Ensure directory exists
        os.makedirs('/home/mosesfdo/Documents/GitHub/moses-fdo/assets', exist_ok=True)
        
        with open('/home/mosesfdo/Documents/GitHub/moses-fdo/assets/heatmap.svg', 'w') as f:
            f.write(svg)
        print("Successfully updated real-time contribution heatmap.")
    except Exception as e:
        print(f"Error updating heatmap: {e}")

if __name__ == '__main__':
    main()
