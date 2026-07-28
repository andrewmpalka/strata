# Secrets and live data

- `.env.demo` is checked in and contains no secrets.
- `.env.live` is human-owned and gitignored; keep it gitignored. Never create,
  edit, display, read, print, echo, log, stage, or commit it.
- Secrets are read only from the runtime environment. Code, images, fixtures,
  tests, reports, command output, and logs must not contain secret values.
- Configuration failures are loud. Do not add credential defaults, guess missing
  values, or turn authorization failures into retry loops.
- Redact credentials from targets, exceptions, and diagnostic output.
- Live data and volumes may be expensive or impossible to reconstruct. Never use
  disposable-environment assumptions for live resources.

If a task appears to require inspecting a human-owned secret file or destructive
work on live data, stop and obtain an explicitly safe alternative.
