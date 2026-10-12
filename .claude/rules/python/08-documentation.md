
# Python documentation

## Docstring format: Google style
- MUST use **Google-style docstrings** for all public modules, classes, methods, and functions.
- MUST document every public function with a clear one-line summary, optional detailed explanation, `Args:`, `Returns:`, and `Raises:` sections where applicable.
- MUST NOT repeat type signatures inside docstring parameter descriptions; type hints in the function signature are the authoritative source of truth.
  ```python
  def calculate_tax(amount: Decimal, rate: Decimal) -> Decimal:
      """Calculate the sales tax for a given amount.

      Args:
          amount: Total transaction subtotal.
          rate: Tax rate percentage expressed as a decimal (e.g. 0.08 for 8%).

      Returns:
          Computed tax rounded to two decimal places.

      Raises:
          ValueError: If the tax rate is negative.
      """
  ```

## Package and module overviews
- Every top-level package or subpackage MUST provide an `__init__.py` with a module-level docstring summarizing its purpose, public exports, and architectural layer.
- MUST define `__all__` in `__init__.py` to explicitly declare the public API contract.

## Documentation generator: MkDocs Material
- Projects publishing documentation SHOULD use **MkDocs** with the **Material for MkDocs** theme and **mkdocstrings** (`mkdocstrings-python`).
- Configuration: `mkdocs.yml` in root with navigation, search, and syntax highlighting enabled.
- Build command: `uv run mkdocs build --strict` (must fail on broken internal links or missing docstrings).

## Architecture Decision Records (ADRs)
- Significant architectural, architectural-layer, or technology choices MUST be documented in `docs/adr/NNNN-title.md`.
- Each ADR must include: Status (Proposed, Accepted, Deprecated, Superseded), Date, Context, Decision, Consequences, and Alternatives Considered.

## Repository README
- The repository root MUST provide a `README.md` containing:
  1. Project purpose and scope.
  2. Quick start instructions with `uv` (`uv sync`).
  3. Key developer commands via `just` (`just ci`, `just test`, `just fmt`).
  4. High-level architecture and directory overview.
