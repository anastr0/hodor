# Hodor [Work in Progress]

Hodor is a learner project designed to explore and implement distributed rate limiting. It serves as a practical example for understanding the concepts and challenges involved in building scalable and efficient rate-limiting systems.

### Problem

In modern systems, APIs need to be scaled automatically. Multiple instances of API servers can run in multiple nodes, and enforcing global ratelimiting rules on autoscaling APIs can be an issue.

Few problems we try to solve in hodor :-

1. Race conditions
    1.1 Maintaining low latency while employing synchronization mechanisms
2. Thundering herd

## Features
- Set rate limiting for FastAPI endpoints (decorators)
    - Define strategy, limits
- Accurate rate limiting with autoscaling
- Fall back mechanisms during high traffic

## Project Structure
```
api/
    main.py          # Entry point for example API
    __init__.py      # Package initialization

hodor/
    config.py        # Configuration management
    decision.py      # Core rate-limiting algorithms and decision engine
    utils.py         # Utility functions to interact with tools and third party services
    wrappers.py      # Wrappers for integrations with APIs

docker-compose.yaml  # Spin up API, redis and other services in containers (Simulation of an actual production system and will be used to test autoscaling setups later)

test/                # Test cases and scripts
```

## Prerequisites
- Python 3.8+
- Docker and Docker Compose

## Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd hodor
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Build and run the Docker containers:
   ```bash
   docker-compose up --build
   ```

## Usage
- Start the application:
  ```bash
  python api/main.py
  ```
- Access the frontend at `http://localhost:8000` (if applicable).

## Roadmap

1. Implement rate limiter library
2. Distributed ID for users per API endpoint
3. Race condition
    - test by spinning up multiple API instances
    - low latency solution
4. Thundering herd problem
    - fall back mechanisms

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests to improve the project.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

