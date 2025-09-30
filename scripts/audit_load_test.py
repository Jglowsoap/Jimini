#!/usr/bin/env python3

import asyncio
import sys
import time
import random
import uuid

# Try to import aiohttp but don't exit if it fails
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    print(
        "Warning: aiohttp package is not installed. Install with: pip install aiohttp"
    )

API_URL = "http://localhost:9000/v1/evaluate"
API_KEY = "changeme"  # Default API key
NUM_REQUESTS = 100
CONCURRENCY = 5

# Sample text payloads to test with
TEXT_SAMPLES = [
    "This is a normal text with no issues.",
    "Here's my API key: api_key=1234567890abcdef",
    "GitHub token: ghp_1234567890abcdefghijkl",
    "A very long text " + "lorem ipsum " * 100,
    "This statement contains potentially hallucinated information: the moon is made of blue cheese.",
]


async def check_server():
    """Check if the server is running by querying health endpoint"""
    if not AIOHTTP_AVAILABLE:
        print("Cannot check server: aiohttp package not installed")
        return False

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9000/health") as response:
                if response.status == 200:
                    return True
    except Exception:  # Fixed: Removed unused variable 'e'
        return False
    return False


async def send_request(session, req_id):
    """Send a test request to the evaluate endpoint"""
    text = random.choice(TEXT_SAMPLES)
    endpoint = f"/api/v1/{random.choice(['chat', 'complete', 'embed'])}"
    direction = random.choice(["inbound", "outbound"])

    payload = {
        "api_key": API_KEY,
        "text": text,
        "endpoint": endpoint,
        "direction": direction,
        "request_id": str(uuid.uuid4()),
    }

    start_time = time.time()
    try:
        async with session.post(API_URL, json=payload) as response:
            data = await response.text()
            duration = time.time() - start_time
            status = response.status
            return req_id, status, duration, data
    except Exception as e:
        duration = time.time() - start_time
        return req_id, 0, duration, str(e)


async def run_load_test(num_requests, concurrency):
    """Run a load test with specified number of requests and concurrency"""
    print(
        f"Starting audit load test with {num_requests} requests ({concurrency} concurrent)..."
    )

    if not AIOHTTP_AVAILABLE:
        print("❌ Cannot run load test: aiohttp package not installed")
        print("Install with: pip install aiohttp")
        return

    # Check if server is running
    server_running = await check_server()
    if not server_running:
        print("❌ Server doesn't appear to be running. Start with:")
        print("uvicorn app.main:app --host 0.0.0.0 --port 9000")
        return

    results = []
    tasks = []

    async with aiohttp.ClientSession() as session:
        for i in range(num_requests):
            task = asyncio.create_task(send_request(session, i))
            tasks.append(task)

            if len(tasks) >= concurrency:
                done, tasks = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED
                )
                results.extend([t.result() for t in done])

        if tasks:
            done, _ = await asyncio.wait(tasks)
            results.extend([t.result() for t in done])

    # Process results
    successful = len([r for r in results if 200 <= r[1] < 300])
    failed = len(results) - successful
    avg_time = sum(r[2] for r in results) / len(results) if results else 0

    print(f"Load test complete: {successful} successful, {failed} failed")
    print(f"Average response time: {avg_time:.4f} seconds")


def main():
    """Main entry point with error handling"""
    if not AIOHTTP_AVAILABLE:
        print("❌ Error: aiohttp package is required for load testing")
        print("Install with: pip install aiohttp")
        print("Skipping load test")
        return 1

    try:
        requests = int(sys.argv[1]) if len(sys.argv) > 1 else NUM_REQUESTS
        concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else CONCURRENCY
        asyncio.run(run_load_test(requests, concurrency))
        return 0
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 0
    except Exception as e:
        print(f"Error running load test: {e}")
        return 1


if __name__ == "__main__":
    # Return status code but don't call sys.exit() which would cause test collection to fail
    status = main()
    if status != 0 and "pytest" not in sys.modules:  # Fixed: Changed to 'not in'
        sys.exit(status)
if __name__ == "__main__":
    # Return status code but don't call sys.exit() which would cause test collection to fail
    status = main()
    if status != 0 and "pytest" not in sys.modules:
        sys.exit(status)
