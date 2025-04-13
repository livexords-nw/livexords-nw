import requests
from collections import defaultdict
from datetime import datetime
import os
from dotenv import load_dotenv

USERNAME = "livexords-nw"
load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
OUTFILE = "LISTREPO.md"

HEADERS = {"Authorization": f"token {TOKEN}"} if TOKEN else {}


def get_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner&sort=full_name"
    repos = requests.get(url, headers=HEADERS).json()
    return repos


def get_commit_count(repo_name, default_branch):
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?per_page=1&sha={default_branch}"
    r = requests.get(url, headers=HEADERS)
    if "Link" in r.headers:
        # Ambil total dari link "last"
        last_link = [
            link for link in r.headers["Link"].split(",") if 'rel="last"' in link
        ]
        if last_link:
            count = int(last_link[0].split("&page=")[-1].split(">")[0])
            return count
    return len(r.json())


def build_markdown(repos):
    grouped = defaultdict(list)
    max_stars_repo = None
    max_commits_repo = None
    max_stars = 0
    max_commits = 0

    for repo in repos:
        name = repo["name"]
        html_url = repo["html_url"]
        stars = repo["stargazers_count"]
        description = repo.get("description") or "No description"
        created = datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ").date()
        updated = datetime.strptime(repo["updated_at"], "%Y-%m-%dT%H:%M:%SZ").date()
        default_branch = repo["default_branch"]
        commits = get_commit_count(name, default_branch)

        repo_data = {
            "name": name,
            "url": html_url,
            "stars": stars,
            "description": description,
            "created": created,
            "updated": updated,
            "commits": commits,
        }

        if stars > max_stars:
            max_stars = stars
            max_stars_repo = repo_data
        if commits > max_commits:
            max_commits = commits
            max_commits_repo = repo_data

        first_letter = name[0].upper()
        grouped[first_letter].append(repo_data)

    # Now build the markdown
    output = []

    if max_stars_repo:
        output.append(f"## 🏆 Most Starred Repo: [{max_stars_repo['name']}]({max_stars_repo['url']})")
        output.append(f"> 🌟 {max_stars_repo['stars']} stars")
        output.append(f"> 📝 {max_stars_repo['description']}")
        output.append(f"> 🧾 Commits: {max_stars_repo['commits']}")
        output.append("")

    if max_commits_repo:
        output.append(f"## 🛠️ Most Committed Repo: [{max_commits_repo['name']}]({max_commits_repo['url']})")
        output.append(f"> 🧾 {max_commits_repo['commits']} commits")
        output.append(f"> 📝 {max_commits_repo['description']}")
        output.append(f"> 🌟 {max_commits_repo['stars']} stars")
        output.append("")

    for letter in sorted(grouped):
        output.append(f"## {letter}")
        for repo in sorted(grouped[letter], key=lambda x: x["name"].lower()):
            output.append(
                f"""### 📦 [{repo['name']}]({repo['url']})  
> 🌟 {repo['stars']} stars • 🔄 Updated: {repo['updated']} • 📅 Created: {repo['created']}  
> 📝 {repo['description']}  
> 🧾 Commits: {repo['commits']}\n"""
            )
        output.append("")

    return "\n".join(output)


def update_readme(content):
    with open(OUTFILE, "r", encoding="utf-8") as f:
        md = f.read()
    import re

    new_md = re.sub(
        r"<!-- START -->(.|\s)*?<!-- END -->",
        f"<!-- START -->\n{content}\n<!-- END -->",
        md,
    )
    with open(OUTFILE, "w", encoding="utf-8") as f:
        f.write(new_md)


if __name__ == "__main__":
    repos = get_repos()
    md = build_markdown(repos)
    update_readme(md)
