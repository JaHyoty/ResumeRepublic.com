"""
Scraper Lambda handler — processes job posting parsing requests.
Invoked asynchronously by the API Lambda via lambda_dispatch.
"""

import json
import asyncio
import structlog

logger = structlog.get_logger()


def handler(event, context):
    """Lambda entry point for job posting scraping."""
    logger.info("Scraper Lambda invoked", payload=event)

    job_posting_id = event.get("job_posting_id")
    if not job_posting_id:
        return {"statusCode": 400, "body": json.dumps({"error": "job_posting_id required"})}

    from app.services.job_posting_parser import JobPostingParserService
    asyncio.run(
        JobPostingParserService.process_job_posting_async(job_posting_id)
    )

    return {"statusCode": 200, "body": json.dumps({"status": "complete"})}
