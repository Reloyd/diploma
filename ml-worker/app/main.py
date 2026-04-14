from fastapi import FastAPI

app = FastAPI(title="Phonoteka ML Worker", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/tasks/status/{task_id}")
def task_status(task_id: str):
    from app.worker import celery_app
    result = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "status": result.status, "result": str(result.result) if result.ready() else None}
