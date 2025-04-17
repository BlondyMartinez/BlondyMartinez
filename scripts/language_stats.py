import os
import requests
import matplotlib.pyplot as plt
from collections import defaultdict

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
USERNAME = os.getenv("GITHUB_USERNAME")

HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
API_URL = "https://api.github.com/graphql"

def run_query(query, variables=None):
    response = requests.post(API_URL, json={'query': query, 'variables': variables}, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_repos_contributed_to():
    repos = []
    has_next_page = True
    end_cursor = None

    query = """
    query ($username: String!, $after: String) {
      user(login: $username) {
        repositoriesContributedTo(first: 100, after: $after, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) {
          pageInfo {
            endCursor
            hasNextPage
          }
          nodes {
            nameWithOwner
            isFork
            languages(first: 10) {
              edges {
                size
                node {
                  name
                }
              }
            }
          }
        }
      }
    }
    """

    while has_next_page:
        result = run_query(query, {"username": USERNAME, "after": end_cursor})
        data = result["data"]["user"]["repositoriesContributedTo"]
        repos += data["nodes"]
        has_next_page = data["pageInfo"]["hasNextPage"]
        end_cursor = data["pageInfo"]["endCursor"]
    return repos

def aggregate_languages(repos):
    language_usage = defaultdict(int)
    for repo in repos:
        for lang in repo["languages"]["edges"]:
            language = lang["node"]["name"]
            size = lang["size"]
            language_usage[language] += size
    return sorted(language_usage.items(), key=lambda x: x[1], reverse=True)

def generate_chart(language_data):
    if not language_data:
        return

    labels, sizes = zip(*language_data[:10])
    colors = plt.get_cmap("tab20").colors

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
    ax.axis("equal")
    plt.title("Languages Used Across Contributions")
    os.makedirs("assets", exist_ok=True)
    plt.savefig("assets/langs.png", bbox_inches='tight')

if __name__ == "__main__":
    repos = get_repos_contributed_to()
    langs = aggregate_languages(repos)
    generate_chart(langs)
