"""
S3 Service for storing and retrieving PDF resumes
"""

import boto3
import os
import uuid
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
            logger.error(f"Failed to upload PDF to S3: {e}")
            logger.error(f"S3 Error Code: {e.response.get('Error', {}).get('Code', 'Unknown')}")
            logger.error(f"S3 Error Message: {e.response.get('Error', {}).get('Message', 'Unknown')}")
            logger.error(f"S3 Request ID: {e.response.get('ResponseMetadata', {}).get('RequestId', 'Unknown')}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading PDF to S3: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            logger.error(f"Failed to upload LaTeX to S3: {e}")
            logger.error(f"S3 Error Code: {e.response.get('Error', {}).get('Code', 'Unknown')}")
            logger.error(f"S3 Error Message: {e.response.get('Error', {}).get('Message', 'Unknown')}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading LaTeX to S3: {e}")
            return None
    
    async def get_pdf_url(self, s3_key: str, expiration: int = 3600, filename: str = None) -> Optional[str]:
        """Generate a secure URL for downloading a PDF via CloudFront signed URLs following AWS documentation"""
        try:
            # Use CloudFront signed URLs if configured for cleaner domain
            if settings.RESUMES_CLOUDFRONT_DOMAIN:
                # Generate CloudFront signed URL using canned policy (AWS recommended approach)
                from cryptography.hazmat.primitives import serialization, hashes
                from cryptography.hazmat.primitives.asymmetric import padding
                from cryptography.hazmat.backends import default_backend
                import datetime
                import os
                import base64
                import urllib.parse
                import json
                
                # CloudFront public key ID (not the random key pair ID)
                # We need to use the actual public key ID that was uploaded to CloudFront
                key_id = settings.CLOUDFRONT_KEY_PAIR_ID
                private_key_path = settings.CLOUDFRONT_PRIVATE_KEY_PATH or '/app/cloudfront_private_key.pem'
                
                logger.info(f"CloudFront signed URL generation: key_id={key_id}, domain={settings.RESUMES_CLOUDFRONT_DOMAIN}")
                
                # Write private key to file if it's in environment variable
                private_key_content = os.getenv('CLOUDFRONT_PRIVATE_KEY')
                if private_key_content and not os.path.exists(private_key_path):
                    os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
                    with open(private_key_path, 'w') as f:
                        f.write(private_key_content)
                
                if key_id and (os.path.exists(private_key_path) or private_key_content):
                    logger.info(f"CloudFront configuration valid: key_id={key_id}, private_key_path={private_key_path}")
                    
                    # Load private key for signing
                    with open(private_key_path, "rb") as key_file:
                        private_key = serialization.load_pem_private_key(
                            key_file.read(), password=None, backend=default_backend()
                        )
                    logger.info("Private key loaded successfully")
                    
                    # Create CloudFront signed URL following AWS documentation
                    # https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-creating-signed-url-canned-policy.html
                    
                    # Step 1: Create the resource URL
                    resource_url = f"https://{settings.RESUMES_CLOUDFRONT_DOMAIN}/{s3_key}"
                    logger.info(f"Generated CloudFront resource URL: {resource_url}")
                    
                    # Step 2: Create the expiration time (Unix timestamp)
                    expiration_time = int((datetime.datetime.utcnow() + datetime.timedelta(seconds=expiration)).timestamp())
                    
                    # Step 3: Create the policy statement (canned policy)
                    policy = {
                        "Statement": [
                            {
                                "Resource": resource_url,
                                "Condition": {
                                    "DateLessThan": {
                                        "AWS:EpochTime": expiration_time
                                    }
                                }
                            }
                        ]
                    }
                    
                    # Step 4: Convert policy to JSON and normalize
                    policy_json = json.dumps(policy, separators=(',', ':'), sort_keys=True)
                    
                    # Step 5: Create the signature
                    signature = private_key.sign(
                        policy_json.encode('utf-8'), 
                        padding.PKCS1v15(), 
                        hashes.SHA1()
                    )
                    
                    # Step 6: Encode policy and signature for URL
                    policy_b64 = base64.b64encode(policy_json.encode('utf-8')).decode('utf-8')
                    signature_b64 = base64.b64encode(signature).decode('utf-8')
                    
                    # Step 7: URL encode the policy and signature
                    policy_url_encoded = urllib.parse.quote(policy_b64, safe='')
                    signature_url_encoded = urllib.parse.quote(signature_b64, safe='')
                    
                    # Step 8: Generate the signed URL
                    signed_url = f"{resource_url}?Policy={policy_url_encoded}&Signature={signature_url_encoded}&Key-Pair-Id={key_id}"
                    
                    logger.info(f"Generated CloudFront signed URL for {s3_key} with expiration {expiration_time}")
                    logger.info(f"Final signed URL: {signed_url}")
                    return signed_url
                else:
                    logger.error(f"CloudFront key pair not configured - key_id={key_id}, private_key_path={private_key_path}, private_key_content_exists={bool(private_key_content)}")
                    return None
            else:
                logger.error(f"CloudFront domain not configured - RESUMES_CLOUDFRONT_DOMAIN={settings.RESUMES_CLOUDFRONT_DOMAIN}")
                return None
        except Exception as e:
            logger.error(f"Failed to generate PDF URL: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    async def get_latex_content(self, s3_key: str) -> Optional[str]:
        """Get LaTeX content from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            return content
        except ClientError as e:
            logger.error(f"Failed to get LaTeX content from S3: {e}")
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
