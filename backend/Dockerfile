# API Lambda — lightweight FastAPI application
# No LaTeX or Playwright — those run in separate worker Lambdas

FROM public.ecr.aws/lambda/python:3.12

# Copy requirements and install Python dependencies (API-only, ~50MB)
COPY requirements-api.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY . ${LAMBDA_TASK_ROOT}/

# Set the Lambda handler
CMD ["lambda_handler.handler"]
