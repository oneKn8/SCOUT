# Contributing to SCOUT Frontend

Thank you for your interest in contributing to SCOUT!

## Development Setup

1. Ensure you have Node.js 20 installed
2. Clone the repository
3. Install dependencies: `npm install`
4. Copy `.env.example` to `.env.local` and configure
5. Start development server: `npm run dev`

## Code Style

- We use ESLint and Prettier for code formatting
- Run `npm run lint` before committing
- Follow Conventional Commits for commit messages

## Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: feat, fix, docs, style, refactor, test, chore

Examples:
- `feat(auth): add login component`
- `fix(ui): resolve button accessibility issue`
- `docs: update README setup instructions`

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure tests pass: `npm test`
4. Ensure linting passes: `npm run lint`
5. Commit using conventional commits
6. Push and create a pull request
7. Fill out the PR template completely

## Testing

- Write tests for new features
- Ensure existing tests pass
- Include accessibility tests where applicable

## Accessibility

This project prioritizes accessibility. Please ensure:
- Proper semantic HTML
- ARIA labels where needed
- Keyboard navigation support
- Color contrast compliance

## Questions?

Feel free to open an issue for questions or discussions.