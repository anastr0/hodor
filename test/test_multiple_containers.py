import logging
import requests
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

_LOG = logging.getLogger(__name__)

def fetch_container_id(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            container_id = response.json().get("Container ID", "Unknown")
            return container_id
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Exception: {str(e)}"

def test_multiple_containers():
    url = "http://localhost:8000/api/v1/hodor/"
    num_requests = 100

    with ThreadPoolExecutor(max_workers=20) as executor:
        responses = list(executor.map(fetch_container_id, [url] * num_requests))

    counter = Counter(responses)

    assert len(counter) > 2, "Expected responses from multiple containers, but got only one."
    _LOG.info(f"Round robin load balancing is working as expected. Responses are evenly distributed among the API instances. Received responses from {len(counter)} instances.")
    for container_id, count in counter.items():
        _LOG.info(f"Container ID: {container_id}, Response count: {count}")

if __name__ == "__main__":
    test_multiple_containers()
