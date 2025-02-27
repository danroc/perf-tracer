from dataclasses import dataclass
from datetime import datetime

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()


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
    duration: float
    end_time: str
    steps: list[EndTraceStep]


@dataclass
class TraceStep:
    step_name: str
    timestamp: datetime
    duration: float


@dataclass
class Trace:
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


traces: dict[str, Trace] = {}


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trace with this tag and trace_id already exists.",
        )

    traces[key] = Trace(start_time=now, steps=[])

    return StartTraceResponse(
        message="Trace started",
        tag=request.tag,
        trace_id=request.trace_id,
        start_time=now.isoformat(),
    )


@app.post("/api/tracing/step")
async def add_step(request: AddStepRequest) -> AddStepResponse:
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

    return AddStepResponse(
        message="Step added",
        tag=request.tag,
        trace_id=request.trace_id,
        step_name=request.step_name,
        timestamp=step.timestamp.isoformat(),
        duration=step.duration,
    )


@app.post("/api/tracing/end")
async def end_trace(request: EndTraceRequest) -> EndTraceResponse:
    """
    End an existing trace.
    """
    now = datetime.now()
    key = build_trace_key(request.tag, request.trace_id)
    trace = traces.pop(key, None)

    if trace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace not found.",
        )

    duration = (now - trace.start_time).total_seconds()

    return EndTraceResponse(
        message="Trace ended",
        tag=request.tag,
        trace_id=request.trace_id,
        duration=duration,
        end_time=now.isoformat(),
        steps=[
            EndTraceStep(
                step_name=step.step_name,
                timestamp=step.timestamp.isoformat(),
                duration=step.duration,
            )
            for step in trace.steps
        ],
    )
