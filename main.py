import logging
from dataclasses import dataclass
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger("uvicorn")

app = FastAPI()


# ----------------------------------------------------------------------
# API models
# ----------------------------------------------------------------------


class StartTraceRequest(BaseModel):
    tag: str
    trace_id: str | None = None


class StartTraceResponse(BaseModel):
    message: str
    tag: str
    trace_id: str | None
    start_time: str


class AddStepRequest(BaseModel):
    tag: str
    trace_id: str | None = None
    step_name: str
    end: bool = False


class AddStepResponse(BaseModel):
    message: str
    tag: str
    trace_id: str | None
    step_name: str
    timestamp: str
    duration: float


class EndTraceRequest(BaseModel):
    tag: str
    trace_id: str | None = None


class EndTraceStep(BaseModel):
    step_name: str
    timestamp: str
    duration: float


class EndTraceResponse(BaseModel):
    message: str
    tag: str
    trace_id: str | None
    start_time: str
    end_time: str
    duration: float
    steps: list[EndTraceStep]


class GetTraceResponse(BaseModel):
    tag: str
    trace_id: str | None
    start_time: str
    end_time: str
    duration: float
    steps: list[EndTraceStep]


# ----------------------------------------------------------------------
# Internal types
# ----------------------------------------------------------------------


@dataclass
class TraceStep:
    step_name: str
    timestamp: datetime
    duration: float


@dataclass
class TraceContext:
    start_time: datetime
    steps: list[TraceStep]

    def _previous_timestamp(self) -> datetime:
        return self.steps[-1].timestamp if self.steps else self.start_time

    def add_step(self, step_name: str, timestamp: datetime) -> TraceStep:
        step = TraceStep(
            step_name=step_name,
            timestamp=timestamp,
            duration=(timestamp - self._previous_timestamp()).total_seconds(),
        )
        self.steps.append(step)
        return step


@dataclass
class TraceResult:
    tag: str
    trace_id: str | None
    start_time: datetime
    end_time: datetime
    duration: float
    steps: list[TraceStep]


# ----------------------------------------------------------------------
# Service state
# ----------------------------------------------------------------------


# tag:trace_id -> TraceContext
traces: dict[str, TraceContext] = {}

# tag -> TraceResult
results: dict[str, list[TraceResult]] = {}


# ----------------------------------------------------------------------
# API endpoints
# ----------------------------------------------------------------------


def build_trace_key(tag: str, trace_id: str | None = None) -> str:
    return f"{tag}:{trace_id or 'default'}"


@app.post("/api/tracing/start")
async def start_trace(request: StartTraceRequest) -> StartTraceResponse:
    """
    Start a new trace.
    """
    now = datetime.now()
    key = build_trace_key(request.tag, request.trace_id)

    if key in traces:
        logger.warning(
            f"Trace with key '{key}' already exists and will be overwritten."
        )

    # NOTE: We overwrite a trace if it already exists
    traces[key] = TraceContext(start_time=now, steps=[])

    return StartTraceResponse(
        message="Trace started",
        tag=request.tag,
        trace_id=request.trace_id,
        start_time=now.isoformat(),
    )


@app.post("/api/tracing/step")
async def add_step(
    request: AddStepRequest,
) -> AddStepResponse | EndTraceResponse:
    """
    Add a step to an existing trace.
    """
    now = datetime.now()
    key = build_trace_key(request.tag, request.trace_id)
    trace = traces.get(key)

    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace not found.",
        )

    step = trace.add_step(request.step_name, now)

    if request.end:
        return await end_trace(
            EndTraceRequest(
                tag=request.tag,
                trace_id=request.trace_id,
            ),
            timestamp=now,
        )

    return AddStepResponse(
        message="Step added",
        tag=request.tag,
        trace_id=request.trace_id,
        step_name=request.step_name,
        timestamp=step.timestamp.isoformat(),
        duration=step.duration,
    )


@app.post("/api/tracing/end")
async def end_trace(
    request: EndTraceRequest, timestamp: datetime | None = None
) -> EndTraceResponse:
    """
    End an existing trace.
    """
    now = timestamp or datetime.now()
    key = build_trace_key(request.tag, request.trace_id)
    trace = traces.pop(key, None)

    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace not found.",
        )

    duration = (now - trace.start_time).total_seconds()

    results.setdefault(request.tag, []).append(
        TraceResult(
            tag=request.tag,
            trace_id=request.trace_id,
            start_time=trace.start_time,
            end_time=now,
            duration=duration,
            steps=trace.steps,
        )
    )

    return EndTraceResponse(
        message="Trace ended",
        tag=request.tag,
        trace_id=request.trace_id,
        start_time=trace.start_time.isoformat(),
        end_time=now.isoformat(),
        duration=duration,
        steps=[
            EndTraceStep(
                step_name=step.step_name,
                timestamp=step.timestamp.isoformat(),
                duration=step.duration,
            )
            for step in trace.steps
        ],
    )


@app.get("/api/traces/{tag}")
async def get_trace(tag: str) -> list[GetTraceResponse]:
    """
    Get all traces for a given tag.
    """
    return [
        GetTraceResponse(
            tag=result.tag,
            trace_id=result.trace_id,
            start_time=result.start_time.isoformat(),
            end_time=result.end_time.isoformat(),
            duration=result.duration,
            steps=[
                EndTraceStep(
                    step_name=step.step_name,
                    timestamp=step.timestamp.isoformat(),
                    duration=step.duration,
                )
                for step in result.steps
            ],
        )
        for result in results.get(tag, [])
    ]


@app.delete("/api/traces/{tag}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trace(tag: str) -> None:
    """
    Delete all traces for a given tag.
    """
    results.pop(tag, None)
