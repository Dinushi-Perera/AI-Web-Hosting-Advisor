# Security Notes

The implementation performs server-side ownership checks even when the UI hides controls. URL analysis permits only HTTP/HTTPS and blocks private, loopback, link-local, reserved and metadata destinations before connecting and again after each redirect. Response sizes, redirects and HTTP timeouts are bounded.

Passwords are bcrypt-hashed through Passlib, access tokens are short-lived JWTs, refresh tokens are stored only as hashes in session records, and password reset records store a nonce hash. Generic login failures avoid user enumeration.

Security-sensitive operations write audit records. Logs and API errors are designed not to expose SQL, stack traces, passwords, cookies, JWTs, API keys or raw `Set-Cookie` evidence.
