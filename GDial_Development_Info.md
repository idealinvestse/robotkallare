# GDial Development Info

## Running the Software
Run the software with logging using the command: 

`./run_with_logging.sh`

This will save all output to **gdial.log** for debugging purposes.

## Software Structure

- **app/**: Contains the main application code, including API endpoints and business logic.
- **tests/**: Contains the test cases to validate the software functionality.

## Development Guidelines
- Ensure all dependencies are listed in **requirements.txt**.
- Follow Python and FastAPI documentation best practices for updates.
- Set environment variables in the **.env** file for secure configuration.
- Use a virtual environment for managing dependencies without affecting the system Python packages.

## Updating Dependencies
When new dependencies are added, update the **requirements.txt** with: 

`pip freeze > requirements.txt`

And test the application thoroughly to ensure no breaking changes have been introduced.
