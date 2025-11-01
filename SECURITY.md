# Security Best Practices in VN PCfix

VN PCfix implements guardrails to reduce risk during troubleshooting and system repair operations.

## Principles
- Least privilege: run as standard user unless an action requires Admin
- Explicit elevation: request elevation via UAC with clear messaging
- Controlled changes: `SupportsShouldProcess` enables `-WhatIf` and confirmation
- Safe logging: write under `%LocalAppData%\PCfix` and avoid sensitive data
- Input validation: sanitize and check parameters and file paths
- No dynamic eval: avoid `Invoke-Expression` and untrusted code execution

## Operational Guidance
- Use `-WhatIf` to dry-run before applying changes
- Prefer the Repairs menu only when elevated
- Review logs after operations for visibility and audit

## Reporting
Please report security concerns via your standard internal process.