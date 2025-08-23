# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Feishu (Lark) Sheets integration toolkit with three main components:

- **FastAPI Application** (`app/`): Web API service with health checks and extensible endpoints
- **Core Library** (`python/`): Minimal FeishuClient for authentication and Sheets operations
- **JSON Schema Services** (`python/json_schema/`): Generate JSON schemas from sheet headers and convert sheet data to structured objects

## Development Setup

### Environment Setup

Set up Python virtual environment and install dependencies:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r app/requirements.txt
pip install -r python/requirements.txt
```

### Feishu Credentials Configuration

Configure Feishu API credentials (choose one method):

1. Environment variables:
```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
```

2. Config file: Edit `python/configs/xpj.feishu.yaml`:
```yaml
auth:
  app_id: "your_app_id"  
  app_secret: "your_app_secret"
```

### Running the Application

Start the FastAPI server:
```bash
uvicorn app.main:app --reload
```

Access health check: http://127.0.0.1:8000/api/v1/health

## Running Tests

Use pytest for testing:
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/clients/test_feishu_client.py

# Run tests with verbose output
pytest -v

# Run the comprehensive integration test suite
python python/test/test.py
```

## Core Architecture

### Dual Structure Design
The project maintains two parallel structures:
- `app/`: FastAPI web service layer with dependency injection
- `python/`: Core library that can be used standalone

### Key Components

**FeishuClient** (`python/core/feishu_client.py`): 
- Minimal Feishu API client using lark-oapi SDK
- Handles authentication via environment variables or config file
- Supports Sheets v3 (list sheets) and v2 (read values) APIs
- Drive v1 API for file listing

**FeishuSchemaService** (`python/json_schema/feishu_service.py`):
- Generates JSON Schema from spreadsheet headers
- Converts sheet data to structured objects
- Supports workbook-level schema aggregation
- Optional disk caching for schemas

**FastAPI Dependency Injection** (`app/main.py`, `app/services/dependencies.py`):
- FeishuClient singleton managed via app.state
- Centralized dependency injection for services
- Redis caching support through service layer

### Data Flow
1. FeishuClient authenticates and fetches sheet data
2. FeishuSchemaService parses headers to generate JSON Schema
3. Raw sheet data converted to typed objects based on schema
4. Results cached (disk for schemas, Redis for data)
5. FastAPI endpoints expose functionality via dependency injection

## Important File Paths

When making changes, be aware of these key locations:
- `app/main.py:19` - FeishuClient initialization
- `python/core/feishu_client.py:29` - Credential loading logic
- `app/services/dependencies.py` - Service dependency injection
- `python/json_schema/config.py` - Schema configuration
- `config/sheet_configs.json` - Sheet processing configurations

## Path Configuration

When using the library standalone, ensure the project root is in PYTHONPATH:
```bash
export PYTHONPATH=$PWD:$PYTHONPATH
```

## Error Handling Patterns

The codebase uses specific error handling patterns:
- RuntimeError for API failures with detailed logging
- NotImplementedError for unsupported SDK features
- Graceful fallbacks for missing dependencies (Redis, cache)
- Comprehensive logging via Python logging module