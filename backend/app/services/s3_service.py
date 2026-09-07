"""
S3 Service for storing and retrieving PDF resumes
"""

import boto3
import os
import uuid
import datetime
import base64
import urllib.parse
import json
from typing import Optional
from botocore.exceptions import ClientError
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        self.bucket_name = settings.RESUMES_S3_BUCKET
        self.region = settings.AWS_REGION
        
        # Debug logging
        logger.info(f"S3Service initialized with bucket: {self.bucket_name}, region: {self.region}")
        
        if not self.bucket_name:
            logger.error("RESUMES_S3_BUCKET is not configured!")
            raise ValueError("RESUMES_S3_BUCKET environment variable is required")
        
        self.s3_client = boto3.client('s3', region_name=self.region)
    
    async def upload_pdf(self, pdf_bytes: bytes, user_id: int, resume_version_id: int, filename: str = None) -> Optional[str]:
        """Upload a PDF to S3 with Content-Disposition header and return the S3 key"""
        try:
            # Create unique S3 key
            s3_key = f"resumes/{user_id}/{resume_version_id}.pdf"
            
            logger.info(f"Attempting to upload PDF to S3: bucket={self.bucket_name}, key={s3_key}")
            logger.info(f"PDF size: {len(pdf_bytes)} bytes, filename: {filename}")
            
            # Prepare upload parameters
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': pdf_bytes,
                'ContentType': 'application/pdf',
                'ServerSideEncryption': 'AES256'
            }
            
            # Add Content-Disposition header if filename is provided
            if filename:
                # Escape quotes in filename to prevent issues
                escaped_filename = filename.replace('"', '\\"')
                upload_params['ContentDisposition'] = f'inline; filename="{escaped_filename}"'
                logger.info(f"Setting Content-Disposition: inline; filename=\"{escaped_filename}\"")
            
            logger.info(f"Upload parameters: {list(upload_params.keys())}")
            
            # Upload to S3
            self.s3_client.put_object(**upload_params)
            
            logger.info(f"PDF uploaded to S3 successfully: {s3_key}")
            return s3_key
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Failed to upload PDF to S3: {error_code}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading PDF to S3: {type(e).__name__}")
            return None
    
    async def upload_latex(self, latex_content: str, user_id: int, resume_version_id: int) -> Optional[str]:
        """Upload a LaTeX file to S3 and return the S3 key"""
        try:
            # Create unique S3 key
            s3_key = f"resumes/{user_id}/{resume_version_id}.tex"
            
            logger.info(f"Attempting to upload LaTeX to S3: bucket={self.bucket_name}, key={s3_key}")
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=latex_content.encode('utf-8'),
                ContentType='text/plain',
                ServerSideEncryption='AES256'
            )
            
            logger.info(f"LaTeX uploaded to S3 successfully: {s3_key}")
            return s3_key
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Failed to upload LaTeX to S3: {error_code}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading LaTeX to S3: {type(e).__name__}")
            return None
    
    def generate_signed_url(self, s3_key: str, expiration: int = 3600, filename: str = None) -> Optional[str]:
        """Generate a presigned S3 URL for downloading/viewing a PDF"""
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'ResponseContentType': 'application/pdf',
            }
            if filename:
                escaped_filename = filename.replace('"', '\\"')
                params['ResponseContentDisposition'] = f'inline; filename="{escaped_filename}"'
            else:
                params['ResponseContentDisposition'] = 'inline'

            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            return None

    async def get_pdf_url(self, s3_key: str, expiration: int = 3600, filename: str = None) -> Optional[str]:
        """Generate a secure presigned URL for viewing/downloading a PDF"""
        return self.generate_signed_url(s3_key, expiration=expiration, filename=filename)
    
    async def get_latex_content(self, s3_key: str) -> Optional[str]:
        """Get LaTeX content from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            return content
        except ClientError as e:
            logger.error(f"Failed to get LaTeX content from S3: {e}")
            return None
    
    async def download_pdf(self, s3_key: str) -> Optional[bytes]:
        """Download PDF content from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            pdf_bytes = response['Body'].read()
            logger.info(f"PDF downloaded from S3: {s3_key}, size: {len(pdf_bytes)} bytes")
            return pdf_bytes
        except ClientError as e:
            logger.error(f"Failed to download PDF from S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF from S3: {e}")
            return None
    
    async def delete_pdf(self, s3_key: str) -> bool:
        """Delete a PDF from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"PDF deleted from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete PDF from S3: {e}")
            return False
    
    async def delete_latex(self, s3_key: str) -> bool:
        """Delete a LaTeX file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"LaTeX file deleted from S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete LaTeX file from S3: {e}")
            return False

# Global instance
s3_service = S3Service()
