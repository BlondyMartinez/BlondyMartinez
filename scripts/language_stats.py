import os
import requests
import matplotlib.pyplot as plt
import seaborn as sns
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

            if language.lower() not in ["hcl", "dockerfile", "yaml", "json"]:
                language_usage[language] += size

    return sorted(language_usage.items(), key=lambda x: x[1], reverse=True)

def generate_svg_chart(language_data):
    if not language_data:
        return

    labels, sizes = zip(*language_data[:10]) 
    plt.figure(figsize=(10, 6))
    sns.barplot(x=list(labels), y=list(sizes), palette="viridis")
    plt.title("Languages Used Across Contributions")
    plt.xlabel("Language")
    plt.ylabel("Bytes of Code")
    plt.xticks(rotation=45, ha="right")

    os.makedirs("assets", exist_ok=True)
    plt.tight_layout()
    plt.savefig("assets/langs.svg", format="svg")
    plt.close()

if __name__ == "__main__":
    repos = get_repos_contributed_to()
    langs = aggregate_languages(repos)
    generate_svg_chart(langs)
