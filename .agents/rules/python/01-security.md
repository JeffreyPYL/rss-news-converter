---
trigger: glob
globs: '**/*.py, pyproject.toml, uv.lock'
---

# Python security

Applies to every Python task. Baseline security rules in `rules/common/01-security-baseline.md` apply universally; this document defines Python-specific language, library, and tool enforcement.

## Secrets and configuration
- MUST NOT commit secrets, tokens, API keys, or `.env` files into source control.
- MUST load secrets and application configuration using `pydantic_settings.BaseSettings` at application startup. Prohibit arbitrary `os.environ` or `os.getenv` calls scattered across business logic.
- MUST wrap all secret fields in `pydantic.SecretStr` (or `pydantic.SecretBytes`). Calling `.get_secret_value()` MUST be deferred to the exact point of external use (e.g. injecting into an HTTP Authorization header).
- MUST NOT log configuration structs containing raw secrets; `SecretStr` formats as `**********` automatically.
- MUST NOT log sensitive request payloads, authorization headers, or PII. Format logs using structured context fields (`logger.info("event", extra={"user_id": user_id})`).

## Deserialization and unsafe execution
- MUST NOT use `pickle`, `marshal`, or `shelve` for untrusted or external data; these permit arbitrary remote code execution. Use JSON or Pydantic models.
- MUST NOT use `yaml.load()` without `Loader=yaml.SafeLoader`; always use `yaml.safe_load()`.
- MUST NOT use `eval()`, `exec()`, or dynamic `__import__()` with dynamic or untrusted strings.
- MUST NOT use `xml.etree.ElementTree` on untrusted input without `defusedxml` protections against entity expansion (Billion Laughs) and external entity injection (XXE).

## Subprocess and command execution
- MUST NOT pass `shell=True` to `subprocess.run`, `subprocess.Popen`, or `os.system`.
- MUST pass arguments to `subprocess` as an explicit sequence of strings (`["executable", "arg1", "arg2"]`). Validate and sanitize all dynamic arguments before execution.

## Database and injection defense
- MUST use parameterized queries or ORM query builders (e.g. SQLAlchemy, SQLModel) with bound parameters. NEVER format SQL queries using `f-strings`, `%`, or `.format()`.
- MUST escape and sanitize any user-controlled input before rendering into HTML, email, or markdown contexts.

## Cryptography and randomness
- MUST use the `secrets` module (`secrets.token_urlsafe()`, `secrets.token_hex()`) for cryptographic tokens, session identifiers, and security nonces. NEVER use the `random` module for security-sensitive values.
- MUST use constant-time comparison (`secrets.compare_digest()`) when verifying tokens, signatures, or message authentication codes.
- MUST use modern cryptographic primitives from `cryptography` or `hashlib` (e.g. `hashlib.sha256()`). NEVER use `md5` or `sha1` for security functions.

## Supply chain and security auditing
- MUST commit `uv.lock` for all applications and services.
- MUST run `uv audit` or `pip-audit` in CI and on a recurring schedule to catch vulnerable dependencies against the GitHub Advisory / PyPA databases.
- MUST run Ruff with the Bandit rule suite (`S` rules) or `bandit -r src/` in CI. Any suppression (`# noqa: S...`) MUST include an adjacent comment stating the justification.
