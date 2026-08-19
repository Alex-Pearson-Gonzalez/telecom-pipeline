from datetime import datetime

# Manual mapping since RIPEstat doesn't return a friendly operator name
ASN_NAMES = {
    "AS3352": "Telefonica de Espana",
    "AS12430": "Vodafone Spain",
    "AS12479": "Orange Spain",
}

def transform_prefix_data(raw_data: dict, asn: str) -> dict:
    """
    Takes the raw RIPEstat JSON and shapes it into a clean dict
    ready for loading into the database.
    """
    prefixes = raw_data["data"]["prefixes"]
    prefix_count = len(prefixes)

    return {
        "asn": asn,
        "operator_name": ASN_NAMES.get(asn, "Unknown"),
        "prefix_count": prefix_count,
        "fetched_at": datetime.now()
    }


if __name__ == "__main__":
    from extract import fetch_prefix_count

    raw = fetch_prefix_count("AS3352")
    clean = transform_prefix_data(raw, "AS3352")
    print(clean)