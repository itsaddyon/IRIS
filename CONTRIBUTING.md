# Contributing

IRIS is a proprietary personal project owned by Adarsh Arya. Contributions, suggestions, and issue reports may be reviewed at the owner's discretion.

## Contribution Rules

- Do not submit secrets, API keys, service-account files, databases, generated reports, model weights, biometric data, or private images.
- Keep changes focused and clearly described.
- Document any change that affects setup, workflow, deployment, or research interpretation.
- Respect the ownership and license terms in `COPYRIGHT.md` and `LICENSE`.

## Development Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The trained model file, private service-account files, and runtime databases are intentionally not included in the repository.

## Reporting Issues

Use the GitHub issue templates and include enough context to reproduce the problem. Remove all private or sensitive information before posting.
