import requests
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

if __name__ == "__main__":
    providers = requests.get('https://releases.hashicorp.com/')
    provider_set= set()
    parsed_html = BeautifulSoup(providers.text)
    for match in parsed_html.body.find_all('a'):
        if match.text.startswith('terraform-provider'):
            provider_set.add(match.text.replace('terraform-provider-',''))

    print(len(provider_set))