from fastapi import FastAPI
import inngest
from inngest.fast_api import serve
import os
from datetime import timedelta

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


@app.get("/health")
def health():
    return {"status": "ok"}


serve(app, inngest_client, [say_hello])