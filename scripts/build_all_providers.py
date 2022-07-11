#!python
import requests

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

if __name__ == "__main__":
    providers = requests.get("https://releases.hashicorp.com/")
    provider_set = set()
    parsed_html = BeautifulSoup(providers.text)
    for match in parsed_html.body.find_all("a"):
        if match.text.startswith("terraform-provider"):
            provider_set.add(match.text.replace("terraform-provider-", ""))
    for provider in provider_set:
        version_set = set()
        if provider != "google":
            continue
        versions = requests.get(
            f"https://releases.hashicorp.com/terraform-provider-{provider}/"
        )
        versions_html = BeautifulSoup(versions.text)
        for match in versions_html.body.find_all("a"):
            if "_" in match.text:
                # terraform-provider-google_4.27.0
                version = match.text.rsplit("_")[1]
                version_set.add(version)

        print(version_set)
