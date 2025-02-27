# perf-tracer

1. Clone this repo

2. Install [uv](https://github.com/astral-sh/uv)

3. Create a `venv` and install the dependencies

   ```bash
   uv venv
   source .venv/bin/activate
   uv sync
   ```

4. Start the server

   ```bash
   fastapi run main.py
   # Or the following during development:
   # fastapi dev main.py
   ```
