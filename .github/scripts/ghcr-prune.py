import argparse
import logging
import requests
import re
import json
from datetime import datetime
from datetime import timedelta


class GHCRPruneError(Exception):
    pass


description = """
This script can be used to prune container images hosted on ghcr.io.\n

Our testing workflow will build and push container images to ghcr.io
that are only used for testing. This script is used to cleanup these
temporary images.

You can filter containers by any combination of name, age, and untagged.
"""

parser = argparse.ArgumentParser(
    description=description, formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument("--token", required=True, help='GitHub token with "repo" scope')
parser.add_argument("--org", required=True, help="Organization name")
parser.add_argument("--name", required=True, help="Package name")
parser.add_argument(
    "--age",
    type=int,
    help="Filter versions by age, removing anything older than",
    default=7,
)
parser.add_argument(
    "--filter", help="Filter which versions are consider for pruning", default=".*"
)
parser.add_argument(
    "--filter-pr",
    action="store_true",
    help="Filter pull requests, will skip removal if pull request is still open.",
)
parser.add_argument("--pr-prefix", default="pr-", help="Prefix for a pull request tag")
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

logger.debug(f"Running with arguments:\n{kwargs}")


class GitHubPaginate:
    """Iterator for GitHub API.

    Provides small wrapper for GitHub API to utilize paging in API calls.

    https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api?apiVersion=2022-11-28
    """

    def __init__(
        self, token, org, name, age, filter, untagged, filter_pr, pr_prefix, **_
    ):
        self.token = token
        self.session = None
        self.url = (
            f"https://api.github.com/orgs/{org}/packages/container/{name}/versions"
        )
        self.pr_url = f"https://api.github.com/repos/{org}/{name}/pulls"
        self.expired = datetime.now() - timedelta(days=age)
        self.filter_pr = filter_pr
        self.pr_prefix = pr_prefix
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

    def is_pr_open(self, pr_number):
        logger.info(f"Checking if PR {pr_number} is still open")

        pr_url = f"{self.pr_url}/{pr_number}"

        response = self.session.get(pr_url)

        response.raise_for_status()

        data = response.json()

        state = data["state"]

        return state == "open"

    def grab_page(self):
        if self.session is None:
            raise GHCRPruneError("Must create session first")

        if self.url is None:
            raise GHCRPruneError("No more pages")

        response = self.session.get(self.url)

        response.raise_for_status()

        remaining = int(response.headers["X-RateLimit-Remaining"])

        logger.debug(f"Remaining api limit {remaining}")

        if remaining <= 0:
            reset = response.headers["X-RateLimit-Reset"]

            raise GHCRPruneError(f"Hit ratelimit will reset at {reset}")

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

        logger.info(f"Expiration date set to {self.expired}")

        for x in data:
            url = x["url"]
            updated_at = datetime.strptime(x["updated_at"], "%Y-%m-%dT%H:%M:%SZ")

            logger.debug(f"Processing\n{json.dumps(x, indent=2)}")

            tags = x["metadata"]["container"]["tags"]

            if len(tags) == 0:
                logger.info(f'Found untagged version {x["id"]}')

                if self.untagged:
                    logger.info(f'Pruning version {x["id"]}')

                    results.append(url)

                continue

            # Any tag that is still valid will cause a pacakge version to not be removed
            remove_package_version = True

            for tag in tags:
                if self.filter_pr and tag.startswith(self.pr_prefix):
                    pr_number = tag[len(self.pr_prefix) :]

                    if self.is_pr_open(pr_number):
                        logger.info(
                            f"Skipping package version {x['id']}, PR {pr_number} is still open"
                        )

                        remove_package_version = False

                        break
                elif self.filter.match(tag) and updated_at > self.expired:
                    logger.info(
                        f"Skipping package version {x['id']}, tag {tag!r} matched but was updated at {updated_at}"
                    )

                    remove_package_version = False

                    break
                else:
                    logger.info(f"Skipping package version {x['id']}, tag {tag!r}")

                    remove_package_version = False

                    break

            if remove_package_version:
                logger.info(f"Pruning package version {x['id']}")

                results.append(url)

        return results

    def __iter__(self):
        self.create_session()

        return self

    def __next__(self):
        if self.page is None or len(self.page) == 0:
            try:
                self.page = self.grab_page()
            except GHCRPruneError as e:
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
    logger.info(f"Pruning {url}")

    if not kwargs["dry_run"]:
        pager.remove_container(url)
