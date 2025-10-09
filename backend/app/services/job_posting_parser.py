"""
Job posting parser service
Orchestrates the parsing pipeline for job postings from URLs
"""

import asyncio
import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import structlog

from app.core.database import SessionLocal
from app.models.job_posting import JobPosting, JobPostingFetchAttempt
from app.services.job_posting_schema_extractor import JobPostingSchemaExtractor
from app.services.job_posting_heuristic_extractor import JobPostingHeuristicExtractor
from app.services.job_posting_web_scraper import JobPostingWebScraper
from app.api.webhooks import (
    send_entity_update,
    send_entity_completed,
    send_entity_failed
)

logger = structlog.get_logger()


class JobPostingParserService:
    """Main service for parsing job postings from URLs"""
    
    def __init__(self):
        self.schema_extractor = JobPostingSchemaExtractor()
        self.heuristic_extractor = JobPostingHeuristicExtractor()
        self.web_scraper = JobPostingWebScraper()
    
    @staticmethod
    async def process_job_posting_async(job_posting_id: str):
        """
        Async background task for FastAPI BackgroundTasks
        Creates its own database session
        """
        db = SessionLocal()
        try:
            await JobPostingParserService.process_job_posting(job_posting_id, db)
        finally:
            db.close()
    
    @staticmethod
    async def process_job_posting(job_posting_id: str, db: Session):
        """
        Background task to process job posting parsing
        Implements two-stage pipeline: schema -> heuristic
        """
        try:
            logger.info("Starting job posting parsing", job_posting_id=job_posting_id)
            
            # Get job posting record
            job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
            if not job_posting:
                logger.error("Job posting not found", job_posting_id=job_posting_id)
                return
            
            # Check if already being processed or completed
            if job_posting.status in ['fetching', 'complete']:
                logger.info("Job posting already processed or being processed", 
                           job_posting_id=job_posting_id, status=job_posting.status)
                return
            
            logger.info("Found job posting, updating status to fetching", 
                       job_posting_id=job_posting_id, url=job_posting.url)
            
            # Update status to fetching (with optimistic locking to prevent race conditions)
            rows_updated = db.query(JobPosting).filter(
                JobPosting.id == job_posting_id,
                JobPosting.status == 'pending'  # Only update if still pending
            ).update({'status': 'fetching'})
            
            if rows_updated == 0:
                logger.info("Job posting status changed by another process", 
                           job_posting_id=job_posting_id)
                return
            
            db.commit()
            
            # Send webhook notification
            if job_posting.created_by_user_id:
                await send_entity_update(
                    job_posting.created_by_user_id,
                    'job_posting',
                    str(job_posting.id),
                    'fetching'
                )
            
            # Create web scraper instance
            web_scraper = JobPostingWebScraper()
            
            # Fetch HTML content once for both extractors
            logger.info("Fetching HTML content", job_posting_id=job_posting_id, url=job_posting.url)
            html_content = await web_scraper.fetch_html(job_posting.url)
            if not html_content:
                logger.error("Failed to fetch HTML content", job_posting_id=job_posting_id, url=job_posting.url)
                await JobPostingParserService._mark_job_posting_failed(job_posting, "Failed to fetch HTML content", db)
                return
            
            logger.info("HTML content fetched successfully", 
                       job_posting_id=job_posting_id, 
                       content_length=len(html_content))
            
            logger.info("Starting Stage 1: Schema extraction", job_posting_id=job_posting_id)
            # Stage 1: Try schema extraction first
            schema_result = await JobPostingParserService._try_schema_extraction(job_posting, html_content, db)
            
            if schema_result and JobPostingParserService._is_valid_result(schema_result):
                await JobPostingParserService._update_job_posting_success(
                    job_posting, schema_result, 'schema', db
                )
                return
            
            # Stage 2: Try heuristic extraction
            heuristic_result = await JobPostingParserService._try_heuristic_extraction(job_posting, html_content, db)
            
            if heuristic_result and JobPostingParserService._is_valid_result(heuristic_result):
                await JobPostingParserService._update_job_posting_success(
                    job_posting, heuristic_result, 'heuristic', db
                )
                return
            
            # Both methods failed
            await JobPostingParserService._mark_job_posting_failed(
                job_posting, "Both extraction methods failed", db
            )
            
        except Exception as e:
            logger.error(
                "Job posting parsing failed",
                job_posting_id=job_posting_id,
                error=str(e)
            )
            try:
                job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
                if job_posting:
                    await JobPostingParserService._mark_job_posting_failed(
                        job_posting, f"Parsing error: {str(e)}", db
                    )
            except Exception as update_error:
                logger.error(
                    "Failed to update job posting status after error",
                    job_posting_id=job_posting_id,
                    error=str(update_error)
                )
    
    @staticmethod
    async def _try_schema_extraction(job_posting: JobPosting, html_content: str, db: Session) -> Optional[Dict[str, Any]]:
        """Try schema-based extraction (JSON-LD, microdata)"""
        start_time = time.time()
        
        try:
            logger.info("Starting schema extraction", job_posting_id=job_posting.id, url=job_posting.url)
            
            # Record attempt
            attempt = JobPostingFetchAttempt(
                job_posting_id=job_posting.id,
                method='schema',
                success=False
            )
            db.add(attempt)
            db.commit()
            
            # Fetch and parse with schema extraction
            logger.info("Calling schema extractor", url=job_posting.url)
            schema_extractor = JobPostingSchemaExtractor()
            result = await schema_extractor.extract_job_data(job_posting.url, html_content)
            
            logger.info("Schema extractor returned", result_found=result is not None)
            if result:
                logger.info("Schema extraction result", 
                           title=result.get('title'),
                           company=result.get('company'),
                           description_length=len(result.get('description', '')),
                           confidence=result.get('confidence'))
            
            # Update attempt record
            attempt.success = result is not None
            attempt.duration_ms = int((time.time() - start_time) * 1000)
            if result:
                attempt.note = f"Extracted: {result.get('title', 'N/A')} at {result.get('company', 'N/A')}"
            else:
                attempt.note = "No structured data found"
            
            db.commit()
            
            logger.info("Schema extraction completed", 
                       success=result is not None,
                       duration_ms=attempt.duration_ms)
            
            return result
            
        except Exception as e:
            logger.error(
                "Schema extraction failed",
                job_posting_id=job_posting.id,
                error=str(e)
            )
            
            # Update attempt record
            attempt.success = False
            attempt.duration_ms = int((time.time() - start_time) * 1000)
            attempt.error_message = str(e)
            db.commit()
            
            return None
    
    @staticmethod
    async def _try_heuristic_extraction(job_posting: JobPosting, html_content: str, db: Session) -> Optional[Dict[str, Any]]:
        """Try heuristic DOM-based extraction"""
        start_time = time.time()
        
        try:
            # Record attempt
            attempt = JobPostingFetchAttempt(
                job_posting_id=job_posting.id,
                method='heuristic',
                success=False
            )
            db.add(attempt)
            db.commit()
            
            # Check for existing domain selectors first (only if domain exists)
            # Fetch and parse with heuristic extraction
            heuristic_extractor = JobPostingHeuristicExtractor()
            result = await heuristic_extractor.extract_job_data(job_posting.url, html_content)
            
            # Update attempt record
            attempt.success = result is not None
            attempt.duration_ms = int((time.time() - start_time) * 1000)
            if result:
                attempt.note = f"Extracted: {result.get('title', 'N/A')} at {result.get('company', 'N/A')}"
            else:
                attempt.note = "Heuristic extraction found no suitable elements"
            
            db.commit()
            return result
            
        except Exception as e:
            logger.error(
                "Heuristic extraction failed",
                job_posting_id=job_posting.id,
                error=str(e)
            )
            
            # Update attempt record
            attempt.success = False
            attempt.duration_ms = int((time.time() - start_time) * 1000)
            attempt.error_message = str(e)
            db.commit()
            
            return None
    
    
    @staticmethod
    def _is_valid_result(result: Dict[str, Any]) -> bool:
        """Validate that extraction result contains required fields"""
        logger.info("Starting result validation", result_keys=list(result.keys()) if result else [])
        
        if not result:
            logger.warning("Result validation failed: result is None or empty")
            return False
        
        # Check for minimum required fields
        title = result.get('title', '').strip()
        description = result.get('description', '').strip()
        
        logger.info("Validation fields", 
                   title=title, 
                   title_length=len(title),
                   description_length=len(description))
        
        # Title must be present and not too short
        if not title or len(title) < 3:
            logger.warning("Result validation failed: invalid title", 
                          title=title, 
                          title_length=len(title),
                          min_length=3)
            return False
        
        # Description must be present and substantial
        if not description or len(description) < 50:
            logger.warning("Result validation failed: invalid description", 
                          description_length=len(description),
                          min_length=50)
            return False
        
        logger.info("Result validation passed", 
                   title=title,
                   title_length=len(title),
                   description_length=len(description))
        
        return True
    
    @staticmethod
    async def _update_job_posting_success(
        job_posting: JobPosting, 
        result: Dict[str, Any], 
        method: str, 
        db: Session
    ):
        """Update job posting with successful extraction results"""
        job_posting.title = result.get('title', '').strip()
        job_posting.company = result.get('company', '').strip()
        job_posting.description = result.get('description', '').strip()
        job_posting.status = 'complete'
        job_posting.provenance = {
            "method": method,
            "extractor": f"{method}_extractor",
            "confidence": result.get('confidence', 0.8),
            "excerpt": result.get('excerpt', '')
        }
        
        # Store raw snapshot if available
        if 'raw_snapshot' in result:
            job_posting.raw_snapshot = result['raw_snapshot']
        
        db.commit()
        
        # Send webhook notification for successful completion
        if job_posting.created_by_user_id:
            await send_entity_completed(
                job_posting.created_by_user_id,
                'job_posting',
                str(job_posting.id),
                {
                    "title": job_posting.title,
                    "company": job_posting.company,
                    "description": job_posting.description,
                    "method": method
                }
            )
        
    
    @staticmethod
    async def _mark_job_posting_failed(
        job_posting: JobPosting, 
        error_message: str, 
        db: Session
    ):
        """Mark job posting as failed with error message"""
        job_posting.status = 'failed'
        job_posting.provenance = {
            "method": "failed",
            "error": error_message
        }
        
        db.commit()
        
        # Send webhook notification for failure
        if job_posting.created_by_user_id:
            await send_entity_failed(
                job_posting.created_by_user_id,
                'job_posting',
                str(job_posting.id),
                error_message
            )
        
