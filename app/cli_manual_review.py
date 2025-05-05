import typer
from sqlmodel import Session
from app.config import get_settings
from app.services.manual_review_service import ManualReviewService

app = typer.Typer()

def get_service():
    session = Session(get_settings().DATABASE_URL)
    return ManualReviewService(session)

@app.command()
def failed():
    """List failed OutboxJobs with contact info."""
    service = get_service()
    results = service.list_failed_jobs()
    for job in results:
        typer.echo(f"Job: {job['job_id']} | Service: {job['service']} | Attempts: {job['attempts']} | Last Error: {job['last_error']}")
        if job['contact']:
            typer.echo(f"  Contact: {job['contact']['name']} <{job['contact']['email']}> | Notes: {job['contact']['notes']}")
        else:
            typer.echo("  Contact: Unknown")
        typer.echo("-")

@app.command()
def mark_sent(job_id: str):
    """Mark a failed job as sent."""
    service = get_service()
    ok = service.mark_sent(job_id)
    if ok:
        typer.echo(f"Job {job_id} marked as sent.")
    else:
        typer.echo(f"Job {job_id} not found.")

@app.command()
def requeue(job_id: str):
    """Requeue a failed job for retry."""
    service = get_service()
    ok = service.requeue(job_id)
    if ok:
        typer.echo(f"Job {job_id} requeued.")
    else:
        typer.echo(f"Job {job_id} not found.")

if __name__ == "__main__":
    app()
