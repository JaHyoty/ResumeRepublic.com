"""
Job posting parser service
Orchestrates the parsing pipeline for job postings from URLs
"""

import asyncio
import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import structlog

from app.models.job_posting import JobPosting, JobPostingFetchAttempt, DomainSelector
from app.services.job_posting_schema_extractor import JobPostingSchemaExtractor
from app.services.job_posting_heuristic_extractor import JobPostingHeuristicExtractor
from app.services.job_posting_web_scraper import JobPostingWebScraper

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
        from app.core.database import SessionLocal
        
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
        logger.info("Starting job posting parsing", job_posting_id=job_posting_id)
        
        try:
            # Get job posting record
            job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
            if not job_posting:
                logger.error("Job posting not found", job_posting_id=job_posting_id)
                return
            
            # Update status to fetching
            job_posting.status = 'fetching'
            db.commit()
            
            # Initialize parser service
            parser_service = JobPostingParserService()
            
            # Stage 1: Try schema extraction first
            schema_result = await parser_service._try_schema_extraction(job_posting, db)
            if schema_result and parser_service._is_valid_result(schema_result):
                await parser_service._update_job_posting_success(
                    job_posting, schema_result, 'schema', db
                )
                logger.info("Schema extraction successful", job_posting_id=job_posting_id)
                return
            
            # Stage 2: Try heuristic extraction
            heuristic_result = await parser_service._try_heuristic_extraction(job_posting, db)
            if heuristic_result and parser_service._is_valid_result(heuristic_result):
                await parser_service._update_job_posting_success(
                    job_posting, heuristic_result, 'heuristic', db
                )
                logger.info("Heuristic extraction successful", job_posting_id=job_posting_id)
                return
            
            # Both methods failed
            await parser_service._mark_job_posting_failed(
                job_posting, "Both extraction methods failed", db
            )
            logger.warning("Both extraction methods failed", job_posting_id=job_posting_id)
            
        except Exception as e:
            logger.error(
                "Job posting parsing failed",
                job_posting_id=job_posting_id,
                error=str(e)
            )
            try:
                job_posting = db.query(JobPosting).filter(JobPosting.id == job_posting_id).first()
                if job_posting:
                    await parser_service._mark_job_posting_failed(
                        job_posting, f"Parsing error: {str(e)}", db
                    )
            except Exception as update_error:
                logger.error(
                    "Failed to update job posting status after error",
                    job_posting_id=job_posting_id,
                    error=str(update_error)
                )
    
    async def _try_schema_extraction(self, job_posting: JobPosting, db: Session) -> Optional[Dict[str, Any]]:
        """Try schema-based extraction (JSON-LD, microdata)"""
        start_time = time.time()
        
        try:
            # Record attempt
            attempt = JobPostingFetchAttempt(
                job_posting_id=job_posting.id,
                method='schema',
                success=False
            )
            db.add(attempt)
            db.commit()
            
            # Fetch and parse with schema extraction
            result = await self.schema_extractor.extract_job_data(job_posting.url)
            
            # Update attempt record
            attempt.success = result is not None
            attempt.duration_ms = int((time.time() - start_time) * 1000)
            if result:
                attempt.note = f"Extracted: {result.get('title', 'N/A')} at {result.get('company', 'N/A')}"
            else:
                attempt.note = "No structured data found"
            
            db.commit()
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
    
    async def _try_heuristic_extraction(self, job_posting: JobPosting, db: Session) -> Optional[Dict[str, Any]]:
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
            domain_selector = None
            if job_posting.domain:
                domain_selector = db.query(DomainSelector).filter(
                    DomainSelector.domain == job_posting.domain
                ).first()
            
            # Fetch and parse with heuristic extraction
            result = await self.heuristic_extractor.extract_job_data(
                job_posting.url, 
                domain_selector.selectors if domain_selector else None
            )
            
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
    
    
    def _is_valid_result(self, result: Dict[str, Any]) -> bool:
        """Validate that extraction result contains required fields"""
        if not result:
            return False
        
        # Check for minimum required fields
        title = result.get('title', '').strip()
        description = result.get('description', '').strip()
        
        # Title must be present and not too short
        if not title or len(title) < 3:
            return False
        
        # Description must be present and substantial
        if not description or len(description) < 50:
            return False
        
        return True
    
    async def _update_job_posting_success(
        self, 
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
            "excerpt": result.get('excerpt', ''),
            "timestamp": job_posting.updated_at.isoformat() if job_posting.updated_at else None
        }
        
        # Store raw snapshot if available
        if 'raw_snapshot' in result:
            job_posting.raw_snapshot = result['raw_snapshot']
        
        db.commit()
        
        # Update domain selector success count if applicable
        if method == 'heuristic' and job_posting.domain:
            domain_selector = db.query(DomainSelector).filter(
                DomainSelector.domain == job_posting.domain
            ).first()
            
            if domain_selector:
                domain_selector.success_count += 1
                domain_selector.last_success = job_posting.updated_at
            else:
                # Create new domain selector record
                domain_selector = DomainSelector(
                    domain=job_posting.domain,
                    selectors=result.get('selectors', []),
                    success_count=1,
                    last_success=job_posting.updated_at
                )
                db.add(domain_selector)
            
            db.commit()
    
    async def _mark_job_posting_failed(
        self, 
        job_posting: JobPosting, 
        error_message: str, 
        db: Session
    ):
        """Mark job posting as failed with error message"""
        job_posting.status = 'failed'
        job_posting.provenance = {
            "method": "failed",
            "error": error_message,
            "timestamp": job_posting.updated_at.isoformat() if job_posting.updated_at else None
        }
        
        db.commit()
        
        # Update domain selector failure count (only if domain exists)
        if job_posting.domain:
            domain_selector = db.query(DomainSelector).filter(
                DomainSelector.domain == job_posting.domain
            ).first()
            
            if domain_selector:
                domain_selector.failure_count += 1
                db.commit()
