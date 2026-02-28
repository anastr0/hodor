import logging
import os
from time import time

# Updated to use multithreading for truly concurrent requests
from concurrent.futures import ThreadPoolExecutor

from collections import Counter


dotenv.load_dotenv()


_LOG = logging.getLogger(__name__)

ENDPOINTS = [
    {"url": "http://localhost:8000/api/v1/hodor/fixed", "method": "GET"},
]


def fetch(session, url, method):
    try:
        response = session.request(method, url)
        return {"url": url, "status": response.status_code, "data": response.text}
    except Exception as e:
        return {"url": url, "error": str(e)}


def load_test(max_requests, max_workers):
    """
    Docstring for load_test

    This function performs a load test on the API endpoints defined in the ENDPOINTS list.
    It uses a ThreadPoolExecutor to send concurrent requests to each endpoint and collects the responses. The results are then aggregated to count the number of responses for each status code and any errors that occurred during the requests.
    """
    import requests
    from time import time

    limit = int(os.environ.get("HODOR_DEFAULT_MAX_REQUESTS"))
    interval = int(os.environ.get("HODOR_DEFAULT_TIME_INTERVAL"))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        with requests.Session() as session:
            tasks = []
            for endpoint in ENDPOINTS:
                for _ in range(max_requests):  # Number of requests per endpoint
                    tasks.append(
                        executor.submit(
                            fetch, session, endpoint["url"], endpoint["method"]
                        )
                    )

            start_time = time()
            responses = [task.result() for task in tasks]
            end_time = time()

            status_counter = Counter()
            for response in responses:
                if "status" in response:
                    status_counter[response["status"]] += 1
                else:
                    status_counter["error"] += 1

            for status, count in status_counter.items():
                print(f"Status {status}: {count} responses")

            print(f"Total time taken: {end_time - start_time} seconds")
            assert (
                status_counter[200] > 0
            ), "Expected some successful responses, but got none."

            # expected_max_success = 1 + ((end_time - start_time + 1) // interval) # Assuming a max of 5 successful requests per second
            # assert status_counter[200] < expected_max_success, f"Expected at most {expected_max_success} successful responses, but got {status_counter[200]} successful responses."

            # TODO : measure success rate
            print(f"Status counter: {status_counter}")
            print(f"Limit: {limit}, Interval: {interval}")
            success_rate = status_counter[200] / (end_time - start_time)
            expected_success_rate = limit / interval
            print(
                f"Success rate: {success_rate}, Expected success rate: {expected_success_rate}"
            )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="URL to test",
        default="http://localhost:8000/api/v1/hodor/fixed",
    )
    # get max number of requests as argument
    parser.add_argument(
        "--max-requests",
        type=int,
        required=True,
        help="Max number of requests to send",
        default=10000,
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        required=True,
        help="Max number of workers to use",
        default=100,
    )
    args = parser.parse_args()
    ENDPOINTS = [{"url": args.url, "method": "GET"}]
    load_test(args.max_requests, args.max_workers)
