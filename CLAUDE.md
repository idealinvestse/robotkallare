# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
- **Start App**: `./run.sh` or `./run_with_logging.sh` (with logging)
- **Run All Tests**: `source venv/bin/activate && python -m pytest`
- **Run Single Test**: `source venv/bin/activate && python -m pytest tests/test_api.py::test_health`
- **Run Test Module**: `source venv/bin/activate && python -m pytest tests/test_api.py`
- **Test Coverage**: `source venv/bin/activate && python -m coverage run -m pytest && python -m coverage report`

## Code Style Guidelines
- **Imports**: Standard lib first, third-party next, local modules last (alphabetically within groups)
- **Types**: Use type hints throughout (Optional, List, etc.); SQLModel for database fields
- **Naming**: Classes=PascalCase, functions/variables=snake_case
- **Error Handling**: Use FastAPI's HTTPException for API errors; Pydantic for validation
- **Functions**: Document key functions with docstrings
- **API Design**: REST API using FastAPI with structured response models 
- **Database**: SQLModel ORM with clear model relationships and UUID primary keys
- **Testing**: Pytest with fixtures for database testing; Mock objects for external dependencies