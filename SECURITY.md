# Security Policy

## Supported Versions

Security fixes are applied to the default branch. Consumers should run the latest commit or latest tagged release when available.

## Reporting a Vulnerability

Do not open a public issue for suspected vulnerabilities. Use GitHub private vulnerability reporting if it is enabled for this repository, or contact the repository owner through their GitHub profile.

Please include:

- A clear description of the issue and affected component
- Reproduction steps or a minimal proof of concept
- Potential impact and any known mitigations
- Whether API keys, exchange credentials, trading signals, or logs may be exposed

## Security Expectations

- Never commit exchange keys, wallet secrets, webhook URLs, or private trading data.
- Keep simulations separated from live execution.
- Run local verification before merging:

```bash
python -m ruff check .
python -m pytest -q
```
