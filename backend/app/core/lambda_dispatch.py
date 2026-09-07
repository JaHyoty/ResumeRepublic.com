"""
Lambda dispatch utility — invokes worker Lambdas for heavy tasks.
Used by the API Lambda to offload PDF generation and web scraping
to dedicated, purpose-built Lambda functions.
"""

import json
import boto3
import structlog
from app.core.settings import settings

logger = structlog.get_logger()

_lambda_client = None


def _get_lambda_client():
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda", region_name=settings.AWS_REGION)
    return _lambda_client


def invoke_pdf_lambda(resume_generation_id: str) -> None:
    """Invoke the PDF Lambda asynchronously to generate a resume."""
    function_name = settings.PDF_LAMBDA_NAME
    if not function_name:
        # Fallback: run in-process (for local dev)
        logger.warning("PDF_LAMBDA_NAME not set, running in-process")
        import asyncio
        from app.services.resume_generation_service import ResumeGenerationService
        asyncio.get_event_loop().create_task(
            ResumeGenerationService.process_resume_generation_async(resume_generation_id)
        )
        return

    payload = {"resume_generation_id": resume_generation_id}
    logger.info("Invoking PDF Lambda", function_name=function_name, payload=payload)
    _get_lambda_client().invoke(
        FunctionName=function_name,
        InvocationType="Event",  # async — fire and forget
        Payload=json.dumps(payload),
    )


def invoke_scraper_lambda(job_posting_id: str) -> None:
    """Invoke the Scraper Lambda asynchronously to parse a job posting."""
    function_name = settings.SCRAPER_LAMBDA_NAME
    if not function_name:
        # Fallback: run in-process (for local dev)
        logger.warning("SCRAPER_LAMBDA_NAME not set, running in-process")
        import asyncio
        from app.services.job_posting_parser import JobPostingParserService
        asyncio.get_event_loop().create_task(
            JobPostingParserService.process_job_posting_async(job_posting_id)
        )
        return

    payload = {"job_posting_id": job_posting_id}
    logger.info("Invoking Scraper Lambda", function_name=function_name, payload=payload)
    _get_lambda_client().invoke(
        FunctionName=function_name,
        InvocationType="Event",  # async — fire and forget
        Payload=json.dumps(payload),
    )


def invoke_pdf_lambda_sync(payload: dict) -> dict:
    """Invoke the PDF Lambda synchronously (for direct LaTeX compilation)."""
    function_name = settings.PDF_LAMBDA_NAME
    if not function_name:
        raise RuntimeError("PDF_LAMBDA_NAME not configured")

    logger.info("Invoking PDF Lambda (sync)", function_name=function_name)
    response = _get_lambda_client().invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    result = json.loads(response["Payload"].read())
    if "errorMessage" in result:
        raise RuntimeError(f"PDF Lambda error: {result['errorMessage']}")
    return result
