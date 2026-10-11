# Production configuration (non-secret, committed; used by GitHub Actions).
# Secrets live in SSM Parameter Store under /resumerepublic/production/*.
# Anything not listed here uses the defaults in variables.tf.

aws_region         = "us-east-1"
project_name       = "resumerepublic"
domain_name        = "resumerepublic.com"
parent_domain_name = "resumerepublic.com"

create_route53_zone       = true
create_www_record         = true
create_cloudfront_records = true
