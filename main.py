from fastapi import FastAPI
import inngest
from inngest.fast_api import serve
import os
from datetime import timedelta
import uuid
from fastapi.responses import JSONResponse
from fastapi import Request

os.environ["INNGEST_DEV"] = "1"

inngest_client = inngest.Inngest(app_id="report-api")


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context):
    await ctx.step.sleep("wait-a-bit", timedelta(seconds=5))

    return "Hello from the background!"


app = FastAPI()
REPORTS = {}

@app.get("/health")
def health():
    return {"status": "ok"}


@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2 
)
async def make_report(ctx: inngest.Context):
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    
    if topic == "fail":
        raise Exception("The report oven is broken!")

    
    await ctx.step.sleep("do-the-slow-work", timedelta(seconds=8))

    def build():
        REPORTS[report_id]["status"] = "done"
        REPORTS[report_id]["result"] = f"A detailed report about {topic}!"
        return REPORTS[report_id]

    await ctx.step.run("build-report", build)
    return "Report finished!"


@app.post("/reports", status_code=202)
async def create_report(request_data: dict):
    
    topic = request_data.get("topic")
    if not topic:
        return JSONResponse(status_code=400, content={"error": "Topic is required"})

    report_id = str(uuid.uuid4())
    
    REPORTS[report_id] = {
        "id": report_id,
        "topic": topic,
        "status": "pending"
    }

    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={"id": report_id, "topic": topic}
        )
    )

    return JSONResponse(status_code=202, content={"id": report_id, "status": "pending"})

@app.get("/reports/{report_id}")
def get_report(report_id: str):
    
    if report_id not in REPORTS:
        return JSONResponse(status_code=404, content={"error": "Report not found"})
    
    
    return REPORTS[report_id]

serve(app, inngest_client, [say_hello, make_report])