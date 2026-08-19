import requests

def fetch_prefix_count(asn: str) -> dict:
    """
    Calls the RIPEstat API for a given ASN and returns the raw JSON response.
    """
    url = "https://stat.ripe.net/data/announced-prefixes/data.json"
    params = {"resource": asn}

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()  # raises an error if the request failed

    return response.json()


if __name__ == "__main__":
    data = fetch_prefix_count("AS3352")
    print(data)