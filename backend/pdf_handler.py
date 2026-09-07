"""
PDF Lambda handler — processes resume generation requests.
Invoked asynchronously by the API Lambda via lambda_dispatch.
"""

import json
import asyncio
import structlog

logger = structlog.get_logger()


def handler(event, context):
    """Lambda entry point for PDF generation."""
    logger.info("PDF Lambda invoked", payload=event)

    # Handle direct invocation (async resume generation)
    resume_generation_id = event.get("resume_generation_id")
    if resume_generation_id:
        from app.services.resume_generation_service import ResumeGenerationService
        asyncio.run(
            ResumeGenerationService.process_resume_generation_async(resume_generation_id)
        )
        return {"statusCode": 200, "body": json.dumps({"status": "complete"})}

    # Handle synchronous LaTeX compilation (for PUT /latex endpoint)
    if event.get("action") == "compile_latex":
        from app.services.latex_service import latex_service, LaTeXCompilationError
        from app.services.s3_service import s3_service
        import tempfile
        import base64
        from pathlib import Path

        latex_content = event["latex_content"]
        user_id = event["user_id"]
        resume_version_id = event["resume_version_id"]

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                tex_file = temp_path / "resume.tex"
                tex_file.write_text(latex_content, encoding="utf-8")
                pdf_file = latex_service.compile_latex(tex_file, temp_path)
                pdf_bytes = pdf_file.read_bytes()

                # Upload to S3
                async def _upload_assets():
                    p_key = await s3_service.upload_pdf(pdf_bytes, user_id, resume_version_id)
                    l_key = await s3_service.upload_latex(latex_content, user_id, resume_version_id)
                    return p_key, l_key

                pdf_s3_key, latex_s3_key = asyncio.run(_upload_assets())

                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "pdf_base64": base64.b64encode(pdf_bytes).decode(),
                        "pdf_s3_key": pdf_s3_key,
                        "latex_s3_key": latex_s3_key,
                    }),
                }
        except LaTeXCompilationError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": str(e)}),
            }

    return {"statusCode": 400, "body": json.dumps({"error": "Unknown action"})}
