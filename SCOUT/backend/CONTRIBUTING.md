# Contributing to SCOUT Backend

Thank you for your interest in contributing to SCOUT!

## Development Setup

1. Ensure you have Python 3.11 installed
2. Clone the repository
3. Create virtual environment: `python -m venv venv`
4. Activate virtual environment: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Copy `.env.example` to `.env` and configure
7. Start services: `docker compose up`

## Code Style

- We use Ruff for linting and Black for formatting
- Run `ruff check .` and `black .` before committing
- Follow Conventional Commits for commit messages

## Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: feat, fix, docs, style, refactor, test, chore

Examples:
- `feat(api): add user authentication endpoint`
- `fix(db): resolve connection pool issue`
- `docs: update API documentation`

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass: `python -m pytest`
4. Ensure linting passes: `ruff check .`
5. Format code: `black .`
6. Commit using conventional commits
7. Push and create a pull request
8. Fill out the PR template completely

## Testing

- Write tests for new features using pytest
- Ensure existing tests pass
- Include integration tests for API endpoints

## Database Changes

- Create migration scripts for schema changes
- Test migrations against sample data
- Document any breaking changes

## Security

- Never commit secrets or credentials
- Use environment variables for configuration
- Follow security best practices for API development

## Questions?

Feel free to open an issue for questions or discussions.