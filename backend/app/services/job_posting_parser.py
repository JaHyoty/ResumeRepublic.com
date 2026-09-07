"""
Job posting parser service — DynamoDB version.
Handles parsing of job postings from URLs with multiple extraction methods.
"""

import asyncio
import time
from typing import Optional, Dict, Any
import structlog

from app.core.dynamodb import get_dynamodb_client, DynamoDBClient
from app.core.dynamodb_models import build_fetch_attempt_item, SK_JOBPOST
from app.services.job_posting_schema_extractor import JobPostingSchemaExtractor
from app.services.job_posting_heuristic_extractor import JobPostingHeuristicExtractor
from app.services.job_posting_web_scraper import JobPostingWebScraper
from app.services.webhook_service import send_entity_completed, send_entity_failed, send_entity_update
from datetime import datetime, timezone

logger = structlog.get_logger()


class JobPostingParserService:
    """Orchestrates job posting parsing with multiple extraction strategies."""

    @staticmethod
    async def process_job_posting_async(job_posting_id: str):
        """Background task entry point."""
        db = get_dynamodb_client()
        await JobPostingParserService.process_job_posting(job_posting_id, db)

    @staticmethod
    async def process_job_posting(job_posting_id: str, db: DynamoDBClient):
        """Process a job posting through extraction pipeline."""
        try:
            logger.info(f"Starting job posting processing, id={job_posting_id}")

            jp = db.get_item(f"JOBPOST#{job_posting_id}", SK_JOBPOST)
            if not jp:
                logger.error(f"Job posting not found: {job_posting_id}")
                return

            url = jp.get("url")
            if not url:
                logger.error(f"Job posting has no URL: {job_posting_id}")
                return

            # Update status to fetching
            db.update_item(f"JOBPOST#{job_posting_id}", SK_JOBPOST, {
                "status": "fetching",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })

            # Fetch HTML content
            scraper = JobPostingWebScraper()
            html_content = await scraper.fetch_html(url)

            if not html_content:
                await JobPostingParserService._mark_job_posting_failed(
                    job_posting_id, jp, "Failed to fetch page content", db,
                )
                return

            # Try extraction methods in order
            result = await JobPostingParserService._try_schema_extraction(
                job_posting_id, url, html_content, db,
            )

            if not result or not JobPostingParserService._is_valid_result(result):
                result = await JobPostingParserService._try_heuristic_extraction(
                    job_posting_id, url, html_content, db,
                )

            if result and JobPostingParserService._is_valid_result(result):
                method = result.get("_method", "schema")
                await JobPostingParserService._update_job_posting_success(
                    job_posting_id, jp, result, method, db,
                )
            else:
                await JobPostingParserService._mark_job_posting_failed(
                    job_posting_id, jp, "All extraction methods failed", db,
                )

        except Exception as e:
            logger.error(f"Job posting processing failed: {str(e)}", job_posting_id=job_posting_id)
            try:
                jp = db.get_item(f"JOBPOST#{job_posting_id}", SK_JOBPOST)
                if jp:
                    await JobPostingParserService._mark_job_posting_failed(
                        job_posting_id, jp, str(e), db,
                    )
            except Exception as update_error:
                logger.error(f"Failed to update status after error: {str(update_error)}")

    @staticmethod
    async def _try_schema_extraction(
        job_posting_id: str, url: str, html_content: str, db: DynamoDBClient,
    ) -> Optional[Dict[str, Any]]:
        """Try schema-based extraction (JSON-LD, microdata)."""
        start_time = time.time()
        attempt_id = db.next_uuid()

        try:
            # Record attempt
            attempt_item = build_fetch_attempt_item(
                job_posting_id=job_posting_id,
                attempt_id=attempt_id,
                method="schema",
                success=False,
            )
            db.put_item(attempt_item)

            schema_extractor = JobPostingSchemaExtractor()
            result = await schema_extractor.extract_job_data(url, html_content)

            duration_ms = int((time.time() - start_time) * 1000)
            success = result is not None

            db.update_item(f"JOBPOST#{job_posting_id}", f"ATTEMPT#{attempt_id}", {
                "success": success,
                "duration_ms": duration_ms,
                "note": f"Extracted: {result.get('title', 'N/A')}" if result else "No structured data found",
            })

            if result:
                result["_method"] = "schema"
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            db.update_item(f"JOBPOST#{job_posting_id}", f"ATTEMPT#{attempt_id}", {
                "success": False,
                "duration_ms": duration_ms,
                "error_message": str(e),
            })
            return None

    @staticmethod
    async def _try_heuristic_extraction(
        job_posting_id: str, url: str, html_content: str, db: DynamoDBClient,
    ) -> Optional[Dict[str, Any]]:
        """Try heuristic DOM-based extraction."""
        start_time = time.time()
        attempt_id = db.next_uuid()

        try:
            attempt_item = build_fetch_attempt_item(
                job_posting_id=job_posting_id,
                attempt_id=attempt_id,
                method="heuristic",
                success=False,
            )
            db.put_item(attempt_item)

            heuristic_extractor = JobPostingHeuristicExtractor()
            result = await heuristic_extractor.extract_job_data(url, html_content)

            duration_ms = int((time.time() - start_time) * 1000)
            success = result is not None

            db.update_item(f"JOBPOST#{job_posting_id}", f"ATTEMPT#{attempt_id}", {
                "success": success,
                "duration_ms": duration_ms,
                "note": f"Extracted: {result.get('title', 'N/A')}" if result else "No data found",
            })

            if result:
                result["_method"] = "heuristic"
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            db.update_item(f"JOBPOST#{job_posting_id}", f"ATTEMPT#{attempt_id}", {
                "success": False,
                "duration_ms": duration_ms,
                "error_message": str(e),
            })
            return None

    @staticmethod
    def _is_valid_result(result: Dict[str, Any]) -> bool:
        """Validate extraction result."""
        if not result:
            return False
        title = result.get("title", "").strip()
        description = result.get("description", "").strip()
        if not title or len(title) < 3:
            return False
        if not description or len(description) < 50:
            return False
        return True

    @staticmethod
    async def _update_job_posting_success(
        job_posting_id: str, jp: dict, result: Dict[str, Any], method: str, db: DynamoDBClient,
    ):
        """Update job posting with successful extraction results."""
        updates = {
            "title": result.get("title", "").strip(),
            "company": result.get("company", "").strip(),
            "description": result.get("description", "").strip(),
            "status": "complete",
            "provenance": {
                "method": method,
                "extractor": f"{method}_extractor",
                "confidence": result.get("confidence", 0.8),
                "excerpt": result.get("excerpt", ""),
            },
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if "raw_snapshot" in result:
            updates["raw_snapshot"] = result["raw_snapshot"]

        db.update_item(f"JOBPOST#{job_posting_id}", SK_JOBPOST, updates)

        user_id = jp.get("created_by_user_id")
        if user_id:
            await send_entity_completed(
                user_id, "job_posting", job_posting_id,
                {"title": updates["title"], "company": updates["company"], "method": method},
            )

    @staticmethod
    async def _mark_job_posting_failed(
        job_posting_id: str, jp: dict, error_message: str, db: DynamoDBClient,
    ):
        """Mark job posting as failed."""
        db.update_item(f"JOBPOST#{job_posting_id}", SK_JOBPOST, {
            "status": "failed",
            "provenance": {"method": "failed", "error": error_message},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })

        user_id = jp.get("created_by_user_id")
        if user_id:
            await send_entity_failed(user_id, "job_posting", job_posting_id, error_message)
