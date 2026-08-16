import urllib.request
import json
import os

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

def generate_svg(stats):
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

def main():
    token = os.environ.get('GITHUB_TOKEN')
    stats = get_stats('moses-fdo', token)
    svg = generate_svg(stats)
    
    os.makedirs('/home/mosesfdo/Documents/GitHub/moses-fdo/assets', exist_ok=True)
    with open('/home/mosesfdo/Documents/GitHub/moses-fdo/assets/stats-card.svg', 'w') as f:
        f.write(svg)
    print("Successfully generated custom stats card.")

if __name__ == '__main__':
    main()
