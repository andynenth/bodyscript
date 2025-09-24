# Disabled Workflows

These workflows were disabled because they reference non-existent components:

## Why Disabled

- **PostgreSQL**: Project doesn't use a database
- **AWS Services**: Not deployed to AWS (ECS, S3, CloudFront, ECR)
- **Test Suites**: No unit/integration tests implemented
- **Dependencies**: Missing tools (pytest, flake8, mypy, safety)
- **Docker**: No Dockerfile.prod exists
- **External Services**: No Slack, Snyk, or CodeQL integration

## Current Architecture

The actual BodyScript project:
- FastAPI backend for video processing
- MediaPipe pose detection
- File-based processing (no database)
- Static frontend (no build process needed)
- Local deployment (no cloud infrastructure)

These workflows can serve as templates if/when these features are added.