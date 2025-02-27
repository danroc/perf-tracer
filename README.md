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
   "tag": "solana-account-creation"
}
```

```http
POST http://localhost:8000/api/tracing/step

{
   "tag": "solana-account-creation",
   "step_name": "click-on-create-account"
}
```

```http
POST http://localhost:8000/api/tracing/step

{
   "tag": "solana-account-creation",
   "step_name": "send-request-to-snap"
}
```

```http
POST http://localhost:8000/api/tracing/step

{
   "tag": "solana-account-creation",
   "step_name": "notify-client"
}
```

```http
POST http://localhost:8000/api/tracing/step

{
   "tag": "solana-account-creation",
   "step_name": "persist-client-state"
}
```

```http
POST http://localhost:8000/api/tracing/step

{
   "tag": "solana-account-creation",
   "step_name": "persist-snap-state",
   "end": true
}
```

```http
POST http://localhost:8000/api/tracing/end

{
   "tag": "solana-account-creation"
}
```

```http
GET http://localhost:8000/api/traces/solana-account-creation
```
