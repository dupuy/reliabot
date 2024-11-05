# Reliabot Security Policy

## Reporting a Vulnerability

Don't report security related issues or vulnerabilities, or include sensitive
information in reports on the issue tracker, or elsewhere in public. Instead,
[open a draft security advisory][1] and provide the relevant information there.

If you don't have a GitHub account or can't use the previous link for any
reason, [contact the author by email][2]. If you can encrypt the email using
their [public key on Keybase][3], or chat using Keybase, that's helpful.

After accepting a vulnerability report, Reliabot maintainers publish it on the
Reliabot [security advisory page][4] once a fix or a mitigation is available.

If the report isn't accepted as a vulnerability, but is a bug or a possible
enhancement, the Reliabot maintainers may open a GitHub issue for tracking it.

## Supported Versions

At this time, only the latest minor version of the 0.x releases of Reliabot get
security updates (0.x.y patch releases) for reported vulnerabilities. Once
there is a 1.x release, this policy would change to account for that.

| Version | Supported |
| ------- | --------- |
| 0.2.x   | ✅        |
| \< 0.2  | ❌        |

[1]: https://github.com/dupuy/reliabot/security/advisories/new
[2]: mailto:alex@dupuy.us
[3]: https://keybase.io/dupuy
[4]: https://github.com/dupuy/reliabot/security/advisories
