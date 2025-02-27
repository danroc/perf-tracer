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

## Examples

```http
POST http://localhost:8000/api/tracing/start

{
   "tag": "my-feature"
}
```

```http
POST http://localhost:8000/api/tracing/step

{
   "tag": "my-feature",
   "step_name": "step-1"
}
```

```http
POST http://localhost:8000/api/tracing/step

{
   "tag": "my-feature",
   "step_name": "step-2"
}
```

```http
POST http://localhost:8000/api/tracing/step

{
   "tag": "my-feature",
   "step_name": "step-3",
   "end": true
}
```

```http
POST http://localhost:8000/api/tracing/end

{
   "tag": "my-feature"
}
```

```http
GET http://localhost:8000/api/traces/my-feature
```

```http
DELETE http://localhost:8000/api/traces/my-feature
```
