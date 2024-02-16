import argparse
import logging
import requests
import re
import json
from datetime import datetime
from datetime import timedelta

description = """
This script can be used to prune container images hosted on ghcr.io.\n

Our testing workflow will build and push container images to ghcr.io
that are only used for testing. This script is used to cleanup these
temporary images.

You can filter containers by any combination of name, age, and untagged.
"""

parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("--token", required=True, help='GitHub token with "repo" scope')
parser.add_argument("--org", required=True, help="Organization name")
parser.add_argument("--name", required=True, help="Package name")
parser.add_argument(
    "--age", type=int, help="Filter versions by age, removing anything older than"
)
parser.add_argument(
    "--filter", help="Filter which versions are consider for pruning", default=".*"
)
parser.add_argument("--untagged", action="store_true", help="Prune untagged versions")
parser.add_argument(
    "--dry-run", action="store_true", help="Does not actually delete anything"
)

logging_group = parser.add_argument_group("logging")
logging_group.add_argument(
    "--log-level", choices=("DEBUG", "INFO", "WARNING", "ERROR"), default="INFO"
)

kwargs = vars(parser.parse_args())

logging.basicConfig(level=kwargs["log_level"])

logger = logging.getLogger("ghcr-prune")


class GitHubPaginate:
    """Iterator for GitHub API.

    Provides small wrapper for GitHub API to utilize paging in API calls.

    https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2022-11-28
    """
    def __init__(self, token, org, name, age, filter, untagged, **_):
        self.token = token
        self.session = None
        self.url = (
            f"https://api.github.com/orgs/{org}/packages/container/{name}/versions"
        )
        self.expired = datetime.now() - timedelta(days=age)
        self.filter = re.compile(filter)
        self.page = None
        self.untagged = untagged

    def create_session(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def grab_page(self):
        if self.session is None:
            raise Exception("Must create session first")

        if self.url is None:
            raise Exception("No more pages")

        response = self.session.get(self.url)

        response.raise_for_status()

        remaining = int(response.headers["X-RateLimit-Remaining"])

        logger.debug(f"Remaining api limit {remaining}")

        if remaining <= 0:
            reset = response.headers["X-RateLimit-Reset"]

            raise Exception(f"Hit ratelimit will reset at {reset}")

        try:
            self.url = self.get_next_url(response.headers["Link"])
        except Exception as e:
            logger.debug(f"No Link header found {e}")

            self.url = None

        return self.filter_results(response.json())

    def get_next_url(self, link):
        match = re.match("<([^>]*)>.*", link)

        if match is None:
            raise Exception("Could not determine next link")

        return match.group(1)

    def filter_results(self, data):
        results = []

        logger.info(f"Processing {len(data)} containers")

        for x in data:
            url = x["url"]
            updated_at = datetime.strptime(x["updated_at"], "%Y-%m-%dT%H:%M:%SZ")

            logger.debug(f"Processing\n{json.dumps(x, indent=2)}")

            try:
                tag = x["metadata"]["container"]["tags"][0]
            except IndexError:
                logger.info(f'Found untagged version {x["id"]}')

                if self.untagged:
                    results.append(url)

                continue

            if not self.filter.match(tag):
                logger.info(f"Skipping {tag}, did not match filter")

                continue

            if updated_at < self.expired:
                logger.info(
                    f"Pruning {tag}, updated at {updated_at}, expiration {self.expired}"
                )

                results.append(url)
            else:
                logger.info(f"Skipping {tag}, more recent than {self.expired}")

        return results

    def __iter__(self):
        self.create_session()

        return self

    def __next__(self):
        if self.page is None or len(self.page) == 0:
            try:
                self.page = self.grab_page()
            except Exception as e:
                logger.debug(f"StopIteration condition {e!r}")

                raise StopIteration from None

        try:
            item = self.page.pop(0)
        except IndexError:
            raise StopIteration from None

        return item

    def remove_container(self, url):
        if self.session is None:
            raise Exception("Must create session first")

        response = self.session.delete(url)

        response.raise_for_status()

        logger.debug(f"{response.headers}")


pager = GitHubPaginate(**kwargs)

for url in pager:
    if kwargs["dry_run"]:
        logger.info(f"Pruning {url}")
    else:
        pager.remove_container(url)
