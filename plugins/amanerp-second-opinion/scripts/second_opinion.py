#!/usr/bin/env python3
"""Safety-first local orchestration for independent second-opinion work."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import math
import os
import re
import selectors
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, NoReturn


PLUGIN_VERSION = "0.2.0"
SCHEMA_VERSION = "2"
MIN_PYTHON = (3, 11)
MIN_CLAUDE = (2, 1, 209)
HIGHEST_TESTED_CLAUDE = (2, 1, 210)
MAX_SINGLE_FILE_BYTES = 6 * 1024 * 1024
MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_CONTEXT_FILES = 32
MAX_STDOUT_BYTES = 16 * 1024 * 1024
MAX_GH_METADATA_BYTES = 1024 * 1024
MAX_PROBE_STDOUT_BYTES = 1024 * 1024
MAX_CHILD_STDERR_BYTES = 1024 * 1024
PROBE_TIMEOUT_SECONDS = 20

EXIT_USAGE = 2
EXIT_DEPENDENCY = 3
EXIT_AUTH = 4
EXIT_CLAUDE = 5
EXIT_TIMEOUT = 6
EXIT_INVALID_RESULT = 7
EXIT_GITHUB = 8
EXIT_INTERNAL = 9

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_ROOT = PLUGIN_ROOT / "references"

REQUIRED_HELP_FLAGS = (
    "--print",
    "--safe-mode",
    "--tools",
    "--no-chrome",
    "--no-session-persistence",
    "--name",
    "--output-format",
    "--verbose",
    "--json-schema",
    "--max-budget-usd",
    "--model",
    "--effort",
)

BASE_CHILD_ENV_ALLOWLIST = frozenset(
    {
        "ALL_PROXY",
        "COLORTERM",
        "CURL_CA_BUNDLE",
        "HOME",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "LOGNAME",
        "NODE_EXTRA_CA_CERTS",
        "NO_COLOR",
        "NO_PROXY",
        "PATH",
        "REQUESTS_CA_BUNDLE",
        "SHELL",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TEMP",
        "TERM",
        "TMP",
        "TMPDIR",
        "TZ",
        "USER",
        "XDG_CONFIG_HOME",
        "all_proxy",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)
CLAUDE_CHILD_ENV_ALLOWLIST = frozenset(
    {"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN"}
)
GITHUB_CHILD_ENV_ALLOWLIST = frozenset(
    {
        "GCM_INTERACTIVE",
        "GH_CONFIG_DIR",
        "GH_ENTERPRISE_TOKEN",
        "GH_HOST",
        "GH_PROMPT_DISABLED",
        "GH_TOKEN",
        "GITHUB_ENTERPRISE_TOKEN",
        "GITHUB_TOKEN",
    }
)
ChildKind = Literal["claude", "github"]

SUPPORTED_SCHEMA_KEYS = {
    "type",
    "required",
    "properties",
    "additionalProperties",
    "enum",
    "items",
    "minItems",
    "maxItems",
    "minimum",
    "maximum",
}

REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)\.(\d+)")
STABLE_RELEASE_TAG_PATTERN = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
MODEL_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

UPDATE_REPOSITORY = "Aman-CERP/amanerp-second-opinion"
UPDATE_ENDPOINT = f"repos/{UPDATE_REPOSITORY}/releases/latest"
GIT_MARKETPLACE_UPDATE_COMMAND = "codex plugin marketplace upgrade amanerp"

QUALITY_PROFILES = ("standard", "deep", "critical")
ADVISORY_PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "standard": {
        "timeout": 900,
        "max_turns": 6,
        "max_budget_usd": 5.0,
        "model": "sonnet",
        "effort": "high",
    },
    "deep": {
        "timeout": 900,
        "max_turns": 6,
        "max_budget_usd": 5.0,
        "model": "opus",
        "effort": "high",
    },
    "critical": {
        "timeout": 1500,
        "max_turns": 10,
        "max_budget_usd": 10.0,
        "model": "opus",
        "effort": "xhigh",
    },
}
PR_PROFILE_DEFAULTS: dict[str, dict[str, Any]] = {
    "standard": {
        "timeout": 1200,
        "max_turns": 8,
        "max_budget_usd": 5.0,
        "model": "sonnet",
        "effort": "high",
    },
    "deep": {
        "timeout": 1200,
        "max_turns": 8,
        "max_budget_usd": 8.0,
        "model": "opus",
        "effort": "high",
    },
    "critical": {
        "timeout": 1500,
        "max_turns": 10,
        "max_budget_usd": 10.0,
        "model": "opus",
        "effort": "xhigh",
    },
}

HIGH_RISK_BASENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "id_rsa",
    "secrets.json",
    "secrets.yaml",
    "secrets.yml",
}
HIGH_RISK_SUFFIXES = {".key", ".p12", ".pfx", ".pem"}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("openai_api_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    (
        "sensitive_diff_path",
        re.compile(
            r"(?m)^diff --git a/(?:.*/)?(?:\.env(?:\.[^ /]+)?|[^ ]+\.(?:pem|key|p12|pfx))\s+b/"
        ),
    ),
)

NAMED_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|private[_-]?key|client[_-]?secret)"
    r"\s*[:=]\s*['\"]?([A-Za-z0-9_./+\-=]{12,})"
)
PLACEHOLDER_VALUES = {
    "changeme",
    "examplevalue",
    "notasecret",
    "placeholder",
    "redacted",
    "replace_me",
}

REDACTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?i)\b(token|secret|password|passwd|api[_-]?key|client[_-]?secret)\s*[:=]\s*\S+"
    ),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{8,}\b"),
    re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
)


class AdvisorError(Exception):
    """Expected error with a stable public exit classification."""

    def __init__(
        self,
        code: int,
        message: str,
        *,
        outcome: str = "error",
        payload: dict[str, Any] | None = None,
        stderr_text: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.public_message = message
        self.outcome = outcome
        self.payload = payload or {}
        self.stderr_text = stderr_text


class BoundedProcessError(Exception):
    """Internal process failure with bounded partial output for classification."""

    def __init__(
        self,
        reason: str,
        *,
        stream_name: str | None = None,
        stdout: bytes = b"",
        stderr: bytes = b"",
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.stream_name = stream_name
        self.stdout = stdout
        self.stderr = stderr


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise AdvisorError(EXIT_USAGE, f"invalid usage: {message}", outcome="rejected")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def diagnostic(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def redact(text: str | bytes | None) -> tuple[str, int]:
    if text is None:
        return "", 0
    if isinstance(text, bytes):
        value = text.decode("utf-8", errors="replace")
    else:
        value = text
    count = 0
    for pattern in REDACTION_PATTERNS:
        value, replacements = pattern.subn("[REDACTED]", value)
        count += replacements
    return value, count


def child_environment(child_kind: ChildKind) -> dict[str, str]:
    credential_allowlist = (
        CLAUDE_CHILD_ENV_ALLOWLIST
        if child_kind == "claude"
        else GITHUB_CHILD_ENV_ALLOWLIST
    )
    allowlist = BASE_CHILD_ENV_ALLOWLIST | credential_allowlist
    env = {name: value for name, value in os.environ.items() if name in allowlist}
    if child_kind == "github":
        env["GH_PROMPT_DISABLED"] = "1"
        env["GCM_INTERACTIVE"] = "Never"
    return env


def kill_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        if process.poll() is None:
            process.kill()
    if process.poll() is None:
        process.wait()


def read_process_chunk(file_descriptor: int) -> bytes:
    return os.read(file_descriptor, 65536)


def run_bounded_process(
    command: list[str],
    *,
    child_kind: ChildKind,
    input_bytes: bytes | None,
    timeout: int,
    max_stdout_bytes: int,
    max_stderr_bytes: int,
) -> tuple[int, bytes, bytes]:
    process: subprocess.Popen[bytes] | None = None
    input_file = None
    selector = selectors.DefaultSelector()
    stdout = bytearray()
    stderr = bytearray()
    deadline = time.monotonic() + timeout
    try:
        stdin_source: Any = subprocess.DEVNULL
        if input_bytes is not None:
            input_file = tempfile.TemporaryFile(mode="w+b")
            input_file.write(input_bytes)
            input_file.seek(0)
            stdin_source = input_file
        process = subprocess.Popen(
            command,
            stdin=stdin_source,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=child_environment(child_kind),
            start_new_session=True,
        )
        if process.stdout is None or process.stderr is None:
            raise BoundedProcessError("start_failed")
        selector.register(
            process.stdout,
            selectors.EVENT_READ,
            (stdout, max_stdout_bytes, "stdout"),
        )
        selector.register(
            process.stderr,
            selectors.EVENT_READ,
            (stderr, max_stderr_bytes, "stderr"),
        )
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BoundedProcessError(
                    "timeout", stdout=bytes(stdout), stderr=bytes(stderr)
                )
            for key, _ in selector.select(timeout=min(remaining, 0.25)):
                target, limit, stream_name = key.data
                chunk = read_process_chunk(key.fileobj.fileno())
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                target.extend(chunk)
                if len(target) > limit:
                    raise BoundedProcessError(
                        "limit",
                        stream_name=stream_name,
                        stdout=bytes(stdout),
                        stderr=bytes(stderr),
                    )
        return_code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        return return_code, bytes(stdout), bytes(stderr)
    except BoundedProcessError:
        if process is not None:
            kill_process_group(process)
        raise
    except subprocess.TimeoutExpired as exc:
        if process is not None:
            kill_process_group(process)
        raise BoundedProcessError(
            "timeout", stdout=bytes(stdout), stderr=bytes(stderr)
        ) from exc
    except OSError as exc:
        reason = "io_error" if process is not None else "start_failed"
        if process is not None:
            kill_process_group(process)
        raise BoundedProcessError(
            reason, stdout=bytes(stdout), stderr=bytes(stderr)
        ) from exc
    finally:
        selector.close()
        if process is not None:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
        if input_file is not None:
            input_file.close()


def resolve_executable(env_name: str, fallback: str) -> str:
    configured = os.environ.get(env_name)
    candidate = configured if configured else shutil.which(fallback)
    if not candidate:
        raise AdvisorError(
            EXIT_DEPENDENCY,
            f"required executable not found: {fallback}",
            outcome="unavailable",
        )
    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise AdvisorError(
            EXIT_DEPENDENCY,
            f"required executable is unavailable: {fallback}",
            outcome="unavailable",
        ) from exc
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        raise AdvisorError(
            EXIT_DEPENDENCY,
            f"required executable is not runnable: {fallback}",
            outcome="unavailable",
        )
    return str(resolved)


def run_probe(
    command: list[str],
    *,
    child_kind: ChildKind,
    timeout: int = PROBE_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    try:
        return_code, stdout, stderr = run_bounded_process(
            command,
            child_kind=child_kind,
            input_bytes=None,
            timeout=timeout,
            max_stdout_bytes=MAX_PROBE_STDOUT_BYTES,
            max_stderr_bytes=MAX_CHILD_STDERR_BYTES,
        )
    except BoundedProcessError as exc:
        if exc.reason == "timeout":
            message = "dependency probe timed out"
        elif exc.reason == "limit":
            message = f"dependency probe {exc.stream_name} exceeded the byte limit"
        elif exc.reason == "io_error":
            message = "dependency probe I/O failed"
        else:
            message = "dependency probe could not start"
        raise AdvisorError(EXIT_DEPENDENCY, message, outcome="unavailable") from exc
    try:
        stdout_text = stdout.decode("utf-8")
        stderr_text = stderr.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdvisorError(
            EXIT_DEPENDENCY,
            "dependency probe output is not valid UTF-8",
            outcome="unavailable",
        ) from exc
    return subprocess.CompletedProcess(
        command, return_code, stdout=stdout_text, stderr=stderr_text
    )


def parse_version(raw: str, dependency: str) -> tuple[int, int, int]:
    match = VERSION_PATTERN.search(raw)
    if not match:
        raise AdvisorError(
            EXIT_DEPENDENCY,
            f"could not parse {dependency} version",
            outcome="unavailable",
        )
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def version_string(value: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in value)


def doctor(*, require_gh: bool, check_update: bool = False) -> dict[str, Any]:
    if sys.version_info < MIN_PYTHON:
        raise AdvisorError(
            EXIT_DEPENDENCY, "Python 3.11 or newer is required", outcome="unavailable"
        )

    claude = resolve_executable("AMANERP_SECOND_OPINION_CLAUDE_BIN", "claude")
    version_result = run_probe([claude, "--version"], child_kind="claude")
    if version_result.returncode != 0:
        raise AdvisorError(
            EXIT_DEPENDENCY, "Claude version probe failed", outcome="unavailable"
        )
    version = parse_version(version_result.stdout, "Claude")
    if version < MIN_CLAUDE:
        raise AdvisorError(
            EXIT_DEPENDENCY,
            f"Claude {version_string(MIN_CLAUDE)} or newer is required",
            outcome="unavailable",
        )

    help_result = run_probe([claude, "--help"], child_kind="claude")
    if help_result.returncode != 0:
        raise AdvisorError(
            EXIT_DEPENDENCY, "Claude help probe failed", outcome="unavailable"
        )
    missing_flags = [
        flag for flag in REQUIRED_HELP_FLAGS if flag not in help_result.stdout
    ]
    if missing_flags:
        raise AdvisorError(
            EXIT_DEPENDENCY,
            "Claude is missing required flag(s): " + ", ".join(missing_flags),
            outcome="unavailable",
        )

    turn_result = run_probe(
        [claude, "--max-turns", "1", "--version"],
        child_kind="claude",
    )
    if turn_result.returncode != 0:
        raise AdvisorError(
            EXIT_DEPENDENCY,
            "Claude does not recognize the required hidden --max-turns control",
            outcome="unavailable",
        )
    turn_probe_version = parse_version(turn_result.stdout, "Claude")
    if turn_probe_version != version:
        raise AdvisorError(
            EXIT_DEPENDENCY,
            "Claude hidden --max-turns probe returned an inconsistent version",
            outcome="unavailable",
        )

    auth_result = run_probe([claude, "auth", "status", "--json"], child_kind="claude")
    try:
        auth_payload = (
            json.loads(auth_result.stdout) if auth_result.stdout.strip() else {}
        )
    except json.JSONDecodeError as exc:
        raise AdvisorError(
            EXIT_AUTH,
            "Claude authentication status was malformed",
            outcome="unavailable",
        ) from exc
    if auth_result.returncode != 0 or auth_payload.get("loggedIn") is not True:
        raise AdvisorError(
            EXIT_AUTH, "Claude is not authenticated", outcome="unavailable"
        )

    warnings: list[str] = []
    if version > HIGHEST_TESTED_CLAUDE:
        warnings.append(
            "Claude is newer than the highest behavior-tested version "
            f"({version_string(HIGHEST_TESTED_CLAUDE)}); rerun the no-tools behavioral smoke."
        )

    result: dict[str, Any] = {
        "status": "ok",
        "plugin_version": PLUGIN_VERSION,
        "python": {
            "version": ".".join(str(part) for part in sys.version_info[:3]),
        },
        "claude": {
            "path": claude,
            "version": version_string(version),
            "authenticated": True,
            "auth_method": auth_payload.get("authMethod"),
            "api_provider": auth_payload.get("apiProvider"),
            "subscription_type": auth_payload.get("subscriptionType"),
            "highest_behavior_tested": version_string(HIGHEST_TESTED_CLAUDE),
        },
        "warnings": warnings,
    }

    if require_gh or check_update:
        gh = resolve_executable("AMANERP_SECOND_OPINION_GH_BIN", "gh")
        gh_version_result = run_probe([gh, "--version"], child_kind="github")
        if gh_version_result.returncode != 0:
            raise AdvisorError(
                EXIT_DEPENDENCY,
                "GitHub CLI version probe failed",
                outcome="unavailable",
            )
        gh_version = parse_version(gh_version_result.stdout, "GitHub CLI")
        gh_auth = run_probe([gh, "auth", "status"], child_kind="github")
        if gh_auth.returncode != 0:
            raise AdvisorError(
                EXIT_AUTH, "GitHub CLI is not authenticated", outcome="unavailable"
            )
        result["github"] = {
            "path": gh,
            "version": version_string(gh_version),
            "authenticated": True,
        }
        if check_update:
            result["update"] = get_update_status(gh)

    return result


def ensure_regular_output_base(raw_path: str | None) -> Path:
    requested = (
        Path(raw_path).expanduser()
        if raw_path
        else Path.cwd() / ".codex" / "amanerp-second-opinion" / "runs"
    )
    if requested.exists() and requested.is_symlink():
        raise AdvisorError(
            EXIT_USAGE, "output directory must not be a symlink", outcome="rejected"
        )
    try:
        canonical = requested.resolve(strict=False)
        canonical.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = canonical.lstat()
    except OSError as exc:
        raise AdvisorError(
            EXIT_USAGE, "output directory cannot be created safely", outcome="rejected"
        ) from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise AdvisorError(
            EXIT_USAGE, "output path is not a safe directory", outcome="rejected"
        )
    try:
        canonical.chmod(0o700)
    except OSError:
        pass
    return canonical


def create_run_dir(base: Path, kind: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for _ in range(8):
        candidate = base / f"{stamp}-{kind}-{secrets.token_hex(4)}"
        try:
            candidate.mkdir(mode=0o700)
            return candidate
        except FileExistsError:
            continue
        except OSError as exc:
            raise AdvisorError(EXIT_INTERNAL, "could not create run directory") from exc
    raise AdvisorError(EXIT_INTERNAL, "could not allocate a unique run directory")


def atomic_write_bytes(path: Path, content: bytes) -> None:
    fd: int | None = None
    temporary: str | None = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            fd = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
        path.chmod(0o600)
    finally:
        if fd is not None:
            os.close(fd)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def atomic_write_text(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(
        path, json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    )


def read_bounded_file(
    raw_path: str, *, label: str, max_bytes: int = MAX_SINGLE_FILE_BYTES
) -> tuple[str, dict[str, Any]]:
    path = Path(raw_path).expanduser()
    if not hasattr(os, "O_NOFOLLOW"):
        raise AdvisorError(
            EXIT_USAGE,
            "this platform cannot safely reject symlink inputs",
            outcome="rejected",
        )
    flags = os.O_RDONLY | os.O_NOFOLLOW
    effective_limit = min(MAX_SINGLE_FILE_BYTES, max_bytes)
    limit_message = (
        f"{label} exceeds the single-file byte limit"
        if max_bytes >= MAX_SINGLE_FILE_BYTES
        else "advisory input exceeds the aggregate byte limit"
    )
    fd: int | None = None
    try:
        fd = os.open(path, flags)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise AdvisorError(
                EXIT_USAGE, f"{label} must be a regular file", outcome="rejected"
            )
        if info.st_size > effective_limit:
            raise AdvisorError(
                EXIT_USAGE,
                limit_message,
                outcome="rejected",
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, min(65536, effective_limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > effective_limit:
                raise AdvisorError(
                    EXIT_USAGE,
                    limit_message,
                    outcome="rejected",
                )
        raw = b"".join(chunks)
    except AdvisorError:
        raise
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.EMLINK):
            raise AdvisorError(
                EXIT_USAGE, f"{label} must not be a symlink", outcome="rejected"
            ) from exc
        raise AdvisorError(
            EXIT_USAGE, f"could not read {label} safely", outcome="rejected"
        ) from exc
    finally:
        if fd is not None:
            os.close(fd)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdvisorError(
            EXIT_USAGE, f"{label} must be valid UTF-8", outcome="rejected"
        ) from exc
    return text, {
        "label": label,
        "path": str(path.absolute()),
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
    }


def risky_path(raw_path: str) -> str | None:
    path = Path(raw_path)
    basename = path.name.lower()
    if basename in HIGH_RISK_BASENAMES or path.suffix.lower() in HIGH_RISK_SUFFIXES:
        return "sensitive_path"
    return None


def scan_sensitive(text: str, source_paths: list[str]) -> list[str]:
    findings: list[str] = []
    for source_path in source_paths:
        category = risky_path(source_path)
        if category and category not in findings:
            findings.append(category)
    for category, pattern in SECRET_PATTERNS:
        if pattern.search(text) and category not in findings:
            findings.append(category)
    for match in NAMED_ASSIGNMENT.finditer(text):
        value = match.group(2).strip("'\"").lower()
        if (
            value not in PLACEHOLDER_VALUES
            and "example" not in value
            and "placeholder" not in value
        ):
            findings.append("named_credential_assignment")
            break
    return findings


def load_reference(name: str) -> str:
    path = REFERENCE_ROOT / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AdvisorError(
            EXIT_INTERNAL, f"bundled reference is unavailable: {name}"
        ) from exc


def load_schema(name: str) -> dict[str, Any]:
    try:
        schema = json.loads(load_reference(name))
    except json.JSONDecodeError as exc:
        raise AdvisorError(
            EXIT_INTERNAL, f"bundled schema is malformed: {name}"
        ) from exc
    validate_schema_definition(schema)
    return schema


def validate_schema_definition(schema: Any, path: str = "$") -> None:
    if not isinstance(schema, dict):
        raise AdvisorError(
            EXIT_INTERNAL, f"bundled schema node is not an object at {path}"
        )
    unsupported = set(schema) - SUPPORTED_SCHEMA_KEYS
    if unsupported:
        raise AdvisorError(
            EXIT_INTERNAL,
            f"unsupported bundled schema keyword at {path}: {sorted(unsupported)[0]}",
        )
    schema_type = schema.get("type")
    if schema_type not in {"object", "array", "string", "integer", "number", "boolean"}:
        raise AdvisorError(EXIT_INTERNAL, f"unsupported bundled schema type at {path}")
    if "enum" in schema and not isinstance(schema["enum"], list):
        raise AdvisorError(EXIT_INTERNAL, f"schema enum must be an array at {path}")
    for key in ("minimum", "maximum"):
        if key in schema and (
            not isinstance(schema[key], (int, float)) or isinstance(schema[key], bool)
        ):
            raise AdvisorError(EXIT_INTERNAL, f"invalid {key} at {path}")
    if schema_type == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if not isinstance(properties, dict) or not isinstance(required, list):
            raise AdvisorError(EXIT_INTERNAL, f"invalid object schema at {path}")
        if schema.get("additionalProperties") is not False:
            raise AdvisorError(EXIT_INTERNAL, f"object schema must be closed at {path}")
        if any(name not in properties for name in required):
            raise AdvisorError(
                EXIT_INTERNAL, f"required property missing from schema at {path}"
            )
        for name, child in properties.items():
            validate_schema_definition(child, f"{path}.{name}")
    if schema_type == "array":
        if "items" not in schema:
            raise AdvisorError(
                EXIT_INTERNAL, f"array schema is missing items at {path}"
            )
        for key in ("minItems", "maxItems"):
            if key in schema and (not isinstance(schema[key], int) or schema[key] < 0):
                raise AdvisorError(EXIT_INTERNAL, f"invalid {key} at {path}")
        validate_schema_definition(schema["items"], f"{path}[]")


def validate_result(value: Any, schema: dict[str, Any], path: str = "$") -> None:
    expected = schema["type"]
    matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }[expected]
    if not matches:
        raise AdvisorError(
            EXIT_INVALID_RESULT,
            f"Claude result has the wrong type at {path}",
            outcome="invalid_result",
        )
    if "enum" in schema and value not in schema["enum"]:
        raise AdvisorError(
            EXIT_INVALID_RESULT,
            f"Claude result has an invalid enum at {path}",
            outcome="invalid_result",
        )
    if "minimum" in schema and value < schema["minimum"]:
        raise AdvisorError(
            EXIT_INVALID_RESULT,
            f"Claude result is below the minimum at {path}",
            outcome="invalid_result",
        )
    if "maximum" in schema and value > schema["maximum"]:
        raise AdvisorError(
            EXIT_INVALID_RESULT,
            f"Claude result is above the maximum at {path}",
            outcome="invalid_result",
        )
    if expected == "object":
        properties = schema["properties"]
        missing = [name for name in schema["required"] if name not in value]
        if missing:
            raise AdvisorError(
                EXIT_INVALID_RESULT,
                f"Claude result is missing {path}.{missing[0]}",
                outcome="invalid_result",
            )
        extras = set(value) - set(properties)
        if extras:
            raise AdvisorError(
                EXIT_INVALID_RESULT,
                f"Claude result has an unexpected property at {path}",
                outcome="invalid_result",
            )
        for name, child in value.items():
            validate_result(child, properties[name], f"{path}.{name}")
    elif expected == "array":
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise AdvisorError(
                EXIT_INVALID_RESULT,
                f"Claude result array is too short at {path}",
                outcome="invalid_result",
            )
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise AdvisorError(
                EXIT_INVALID_RESULT,
                f"Claude result array is too long at {path}",
                outcome="invalid_result",
            )
        for index, child in enumerate(value):
            validate_result(child, schema["items"], f"{path}[{index}]")


def validate_common_options(
    args: argparse.Namespace, *, profiles: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    quality = args.quality or "deep"
    defaults = profiles[quality]
    standard_acknowledged = bool(args.acknowledge_standard_quality)
    if quality == "standard" and not standard_acknowledged:
        raise AdvisorError(
            EXIT_USAGE,
            "--quality standard requires --acknowledge-standard-quality",
            outcome="rejected",
        )
    if quality != "standard" and standard_acknowledged:
        raise AdvisorError(
            EXIT_USAGE,
            "--acknowledge-standard-quality is only valid with --quality standard",
            outcome="rejected",
        )
    timeout = args.timeout if args.timeout is not None else defaults["timeout"]
    turns = args.max_turns if args.max_turns is not None else defaults["max_turns"]
    budget = (
        args.max_budget_usd
        if args.max_budget_usd is not None
        else defaults["max_budget_usd"]
    )
    model = defaults["model"]
    effort = defaults["effort"]
    if not 60 <= timeout <= 1800:
        raise AdvisorError(
            EXIT_USAGE,
            "timeout must be between 60 and 1800 seconds",
            outcome="rejected",
        )
    if not 1 <= turns <= 12:
        raise AdvisorError(
            EXIT_USAGE, "max turns must be between 1 and 12", outcome="rejected"
        )
    if not 0.10 <= budget <= 20.00:
        raise AdvisorError(
            EXIT_USAGE,
            "max budget must be between USD 0.10 and USD 20.00",
            outcome="rejected",
        )
    return {
        "timeout": timeout,
        "max_turns": turns,
        "max_budget_usd": budget,
        "model": model,
        "effort": effort,
        "quality_profile": quality,
        "standard_quality_acknowledged": standard_acknowledged,
    }


def assemble_untrusted_input(payload: dict[str, Any]) -> str:
    return (
        "<<<AMANERP_SECOND_OPINION_UNTRUSTED_INPUT_V1>>>\n"
        + json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
        + "\n<<<END_AMANERP_SECOND_OPINION_UNTRUSTED_INPUT_V1>>>\n"
    )


def extract_structured_output(envelope: Any) -> dict[str, Any]:
    if not isinstance(envelope, dict):
        raise AdvisorError(
            EXIT_INVALID_RESULT,
            "Claude response envelope is not an object",
            outcome="invalid_result",
        )
    if envelope.get("is_error") is True or envelope.get("subtype") not in (
        None,
        "success",
    ):
        raise AdvisorError(
            EXIT_CLAUDE,
            "Claude reported an unsuccessful result",
            outcome="claude_failed",
        )
    structured = envelope.get("structured_output")
    if structured is None and isinstance(envelope.get("result"), str):
        try:
            structured = json.loads(envelope["result"])
        except json.JSONDecodeError:
            structured = None
    if not isinstance(structured, dict):
        raise AdvisorError(
            EXIT_INVALID_RESULT,
            "Claude response did not contain structured output",
            outcome="invalid_result",
        )
    return structured


def parse_claude_stream(raw: bytes) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdvisorError(
            EXIT_INVALID_RESULT,
            "Claude response is not valid UTF-8",
            outcome="invalid_result",
        ) from exc
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdvisorError(
                EXIT_INVALID_RESULT,
                f"Claude stream event {line_number} is not valid JSON",
                outcome="invalid_result",
            ) from exc
        if not isinstance(event, dict):
            raise AdvisorError(
                EXIT_INVALID_RESULT,
                f"Claude stream event {line_number} is not an object",
                outcome="invalid_result",
            )
        events.append(event)
    terminal_events = [event for event in events if event.get("type") == "result"]
    if len(terminal_events) != 1:
        raise AdvisorError(
            EXIT_INVALID_RESULT,
            "Claude stream did not contain exactly one terminal result",
            outcome="invalid_result",
        )
    return events, terminal_events[0]


def safe_model_id(value: Any) -> str | None:
    return (
        value if isinstance(value, str) and MODEL_ID_PATTERN.fullmatch(value) else None
    )


def valid_nonnegative_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def valid_nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def model_matches_family(model: str, family: str) -> bool:
    return model == family or model.startswith(f"claude-{family}-")


def collect_model_telemetry(
    events: list[dict[str, Any]],
    envelope: dict[str, Any],
    *,
    requested_family: str,
) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    initialized_models: set[str] = set()
    assistant_models: set[str] = set()

    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            model = safe_model_id(event.get("model"))
            if model is None:
                issues.append("initialization model is missing or invalid")
            else:
                initialized_models.add(model)
        if event.get("type") == "assistant":
            message = event.get("message")
            model = safe_model_id(
                message.get("model") if isinstance(message, dict) else None
            )
            if model is None:
                issues.append("assistant model is missing or invalid")
            else:
                assistant_models.add(model)

    if len(initialized_models) != 1:
        issues.append("exactly one initialization model is required")
    if len(assistant_models) != 1:
        issues.append("exactly one answering model is required")

    initialized_model = (
        next(iter(initialized_models)) if len(initialized_models) == 1 else None
    )
    primary_model = next(iter(assistant_models)) if len(assistant_models) == 1 else None
    if initialized_model and not model_matches_family(
        initialized_model, requested_family
    ):
        issues.append(
            "initialization model does not match the requested quality profile"
        )
    if primary_model and not model_matches_family(primary_model, requested_family):
        issues.append("answering model does not match the requested quality profile")

    raw_usage = envelope.get("modelUsage")
    usage_by_model: dict[str, Any] = {}
    if not isinstance(raw_usage, dict):
        issues.append("model usage is missing or invalid")
    else:
        for raw_model, usage in raw_usage.items():
            model = safe_model_id(raw_model)
            if model is None:
                issues.append("model usage contains an invalid model identifier")
                continue
            usage_by_model[model] = usage

    observed_models = initialized_models | assistant_models | set(usage_by_model)
    primary_family_models = sorted(
        model
        for model in observed_models
        if model_matches_family(model, requested_family)
    )
    auxiliary_models = sorted(
        model
        for model in observed_models
        if not model_matches_family(model, requested_family)
    )
    if primary_model and not any(
        model_matches_family(model, requested_family) for model in usage_by_model
    ):
        issues.append("requested model family is absent from model usage")
    if auxiliary_models:
        issues.append("auxiliary model usage is not permitted")

    normalized_usage: list[dict[str, Any]] = []
    for model in sorted(usage_by_model):
        usage = usage_by_model[model]
        if not isinstance(usage, dict):
            issues.append("per-model usage is invalid")
            continue
        input_tokens = usage.get("inputTokens")
        output_tokens = usage.get("outputTokens")
        cost_usd = usage.get("costUSD")
        if not valid_nonnegative_integer(input_tokens):
            issues.append("per-model input token usage is invalid")
        if not valid_nonnegative_integer(output_tokens):
            issues.append("per-model output token usage is invalid")
        if not valid_nonnegative_number(cost_usd):
            issues.append("per-model cost usage is invalid")
        normalized_usage.append(
            {
                "model": model,
                "role": "primary"
                if model_matches_family(model, requested_family)
                else "auxiliary",
                "input_tokens": input_tokens
                if valid_nonnegative_integer(input_tokens)
                else None,
                "output_tokens": output_tokens
                if valid_nonnegative_integer(output_tokens)
                else None,
                "cache_read_input_tokens": usage.get("cacheReadInputTokens")
                if valid_nonnegative_integer(usage.get("cacheReadInputTokens"))
                else 0,
                "cache_creation_input_tokens": usage.get("cacheCreationInputTokens")
                if valid_nonnegative_integer(usage.get("cacheCreationInputTokens"))
                else 0,
                "cost_usd": cost_usd if valid_nonnegative_number(cost_usd) else None,
            }
        )

    telemetry = {
        "initialized_model_observed": initialized_model,
        "assistant_models_observed": sorted(assistant_models),
        "primary_model_observed": primary_model,
        "primary_family_models_observed": primary_family_models,
        "auxiliary_models_observed": auxiliary_models,
        "models_observed": sorted(observed_models),
        "resolved_models": sorted(observed_models),
        "model_usage": normalized_usage,
        "model_policy_verified": not issues,
    }
    return telemetry, list(dict.fromkeys(issues))


def summarize_failed_stream(raw: bytes, *, exit_code: int) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    events: list[dict[str, Any]] = []
    malformed_lines = 0
    event_types: dict[str, int] = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            malformed_lines += 1
            continue
        if not isinstance(event, dict):
            malformed_lines += 1
            continue
        events.append(event)
        event_type = event.get("type")
        if not (
            isinstance(event_type, str)
            and re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", event_type)
        ):
            event_type = "unknown"
        event_types[event_type] = event_types.get(event_type, 0) + 1

    terminal = next(
        (event for event in reversed(events) if event.get("type") == "result"), None
    )
    safe_terminal: dict[str, Any] = {}
    terminal_redactions = 0
    if terminal is not None:
        for key in (
            "subtype",
            "is_error",
            "api_error_status",
            "terminal_reason",
            "stop_reason",
            "session_id",
        ):
            value = terminal.get(key)
            if isinstance(value, str) and len(value) <= 256:
                value, redactions = redact(value)
                terminal_redactions += redactions
                safe_terminal[key] = value
            elif isinstance(value, (bool, int)) or (
                isinstance(value, float) and math.isfinite(value)
            ):
                safe_terminal[key] = value

    observed_models: set[str] = set()
    for event in events:
        candidates: list[Any] = []
        if event.get("type") == "system":
            candidates.append(event.get("model"))
        if event.get("type") == "assistant" and isinstance(event.get("message"), dict):
            candidates.append(event["message"].get("model"))
        if event.get("type") == "result" and isinstance(event.get("modelUsage"), dict):
            candidates.extend(event["modelUsage"].keys())
        observed_models.update(
            model for candidate in candidates if (model := safe_model_id(candidate))
        )

    error_message = terminal.get("result") if terminal else None
    sanitized_error, error_redactions = redact(
        error_message[:4096] if isinstance(error_message, str) else ""
    )
    return {
        "exit_code": exit_code,
        "stdout_bytes": len(raw),
        "event_count": len(events),
        "malformed_event_lines": malformed_lines,
        "event_types": dict(sorted(event_types.items())),
        "terminal": safe_terminal,
        "terminal_redactions": terminal_redactions,
        "models_observed": sorted(observed_models),
        "error": sanitized_error,
        "error_redactions": error_redactions,
    }


def render_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None reported."]


def render_advisory(result: dict[str, Any]) -> str:
    recommendation = result["recommendation"]
    lines = [
        "# Claude advisory",
        "",
        f"Status: **{result['status']}**  ",
        f"Confidence: **{recommendation['confidence']}**",
        "",
        "## Executive summary",
        "",
        result["executive_summary"],
        "",
        "## Recommendation",
        "",
        f"**{recommendation['choice']}** — {recommendation['rationale']}",
        "",
        "### Conditions that would change it",
        "",
        *render_list(recommendation["conditions_that_change_it"]),
        "",
        "## Facts",
        "",
    ]
    for fact in result["facts"]:
        evidence = (
            ", ".join(fact["evidence"]) if fact["evidence"] else "no evidence reference"
        )
        lines.append(f"- {fact['claim']} _(evidence: {evidence})_")
    if not result["facts"]:
        lines.append("- None established.")
    lines.extend(["", "## Options", ""])
    for option in result["options"]:
        lines.extend(
            [
                f"### {option['name']}",
                "",
                "Benefits:",
                *render_list(option["benefits"]),
                "",
                "Drawbacks:",
                *render_list(option["drawbacks"]),
                "",
                "Risks:",
                *render_list(option["risks"]),
                "",
            ]
        )
    lines.extend(
        [
            "## Material risks",
            "",
            *render_list(result["material_risks"]),
            "",
            "## Assumptions",
            "",
            *render_list(result["assumptions"]),
            "",
            "## Open questions",
            "",
            *render_list(result["open_questions"]),
            "",
            "## Validation steps",
            "",
            *render_list(result["validation_steps"]),
            "",
        ]
    )
    return "\n".join(lines)


def render_pr_review(result: dict[str, Any]) -> str:
    lines = [
        "# Claude pull-request review",
        "",
        f"Verdict: **{result['verdict']}**  ",
        f"Confidence: **{result['confidence']}**",
        "",
        "## Summary",
        "",
        result["summary"],
        "",
        "## Findings",
        "",
    ]
    if not result["findings"]:
        lines.append("No actionable findings reported.")
    for finding in result["findings"]:
        location = finding["file"]
        if "line" in finding:
            location += f":{finding['line']}"
        lines.extend(
            [
                f"### [{finding['severity'].upper()}] {finding['title']}",
                "",
                f"- ID: `{finding['id']}`",
                f"- Location: `{location}`",
                f"- Category: `{finding['category']}`",
                f"- Confidence: `{finding['confidence']}`",
                f"- Evidence: {finding['evidence']}",
                f"- Failure scenario: {finding['failure_scenario']}",
                f"- Impact: {finding['impact']}",
                f"- Recommended fix: {finding['recommended_fix']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Residual risks",
            "",
            *render_list(result["residual_risks"]),
            "",
            "## Verification gaps",
            "",
            *render_list(result["verification_gaps"]),
            "",
        ]
    )
    return "\n".join(lines)


def execute_claude(
    *,
    kind: str,
    prompt_name: str,
    schema_name: str,
    payload: dict[str, Any],
    request: dict[str, Any],
    source: dict[str, Any],
    limits: dict[str, Any],
    output_dir: str | None,
    sensitive_override: bool,
    sensitive_findings: list[str],
    doctor_result: dict[str, Any],
) -> dict[str, Any]:
    prompt = load_reference(prompt_name).strip()
    schema = load_schema(schema_name)
    untrusted_input = assemble_untrusted_input(payload)
    full_input_hash = sha256_text(prompt + "\0" + untrusted_input)
    if len(untrusted_input.encode("utf-8")) > MAX_INPUT_BYTES:
        raise AdvisorError(
            EXIT_USAGE,
            "assembled input exceeds the total byte limit",
            outcome="rejected",
        )

    base = ensure_regular_output_base(output_dir)
    run_dir = create_run_dir(base, kind)
    started = utc_now()
    start_monotonic = time.monotonic()
    receipt: dict[str, Any] = {
        "plugin_version": PLUGIN_VERSION,
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "started_at": started,
        "outcome": "running",
        "claude": {
            "path": doctor_result["claude"]["path"],
            "version": doctor_result["claude"]["version"],
            "highest_behavior_tested": doctor_result["claude"][
                "highest_behavior_tested"
            ],
            "quality_profile": limits["quality_profile"],
            "model_requested": limits["model"],
            "effort": limits["effort"],
            "standard_quality_acknowledged": limits["standard_quality_acknowledged"],
        },
        "resource_limits": {
            "timeout_seconds": limits["timeout"],
            "max_turns": limits["max_turns"],
            "budget_requested_usd": limits["max_budget_usd"],
            "max_input_bytes": MAX_INPUT_BYTES,
        },
        "controls": {
            "safe_mode": True,
            "tools_disabled": True,
            "chrome_disabled": True,
            "session_persistence_disabled": True,
            "shell_disabled": True,
            "sensitive_input_override": sensitive_override,
            "sensitive_categories": sensitive_findings,
        },
        "source": source,
        "input_sha256": full_input_hash,
        "warnings": doctor_result.get("warnings", []),
        "artifacts": {},
    }

    request_path = run_dir / "request.json"
    input_hash_path = run_dir / "input.sha256"
    stderr_path = run_dir / "stderr.log"
    receipt_path = run_dir / "receipt.json"
    atomic_write_json(request_path, request)
    atomic_write_text(input_hash_path, full_input_hash + "\n")
    atomic_write_text(stderr_path, "")
    receipt["artifacts"] = {
        "request": str(request_path),
        "input_hash": str(input_hash_path),
        "stderr": str(stderr_path),
        "receipt": str(receipt_path),
    }

    command = [
        doctor_result["claude"]["path"],
        "--print",
        "--safe-mode",
        "--tools",
        "",
        "--no-chrome",
        "--no-session-persistence",
        "--name",
        f"amanerp-second-opinion-{kind}",
        "--output-format",
        "stream-json",
        "--verbose",
        "--json-schema",
        compact_json(schema),
        "--max-turns",
        str(limits["max_turns"]),
        "--max-budget-usd",
        f"{limits['max_budget_usd']:.2f}",
        "--model",
        limits["model"],
        "--effort",
        limits["effort"],
        prompt,
    ]

    try:
        try:
            claude_exit_code, claude_stdout, claude_stderr = run_bounded_process(
                command,
                child_kind="claude",
                input_bytes=untrusted_input.encode("utf-8"),
                timeout=limits["timeout"],
                max_stdout_bytes=MAX_STDOUT_BYTES,
                max_stderr_bytes=MAX_CHILD_STDERR_BYTES,
            )
        except BoundedProcessError as exc:
            timeout_stderr, redactions = redact(exc.stderr)
            atomic_write_text(stderr_path, timeout_stderr)
            receipt["stderr_redactions"] = redactions
            if exc.reason == "limit" and exc.stream_name == "stdout":
                raise AdvisorError(
                    EXIT_INVALID_RESULT,
                    "Claude response exceeds the output byte limit",
                    outcome="invalid_result",
                    stderr_text=timeout_stderr,
                ) from exc
            if exc.reason == "limit":
                raise AdvisorError(
                    EXIT_CLAUDE,
                    "Claude diagnostics exceeded the output byte limit",
                    outcome="claude_failed",
                    stderr_text=timeout_stderr,
                ) from exc
            if exc.reason == "start_failed":
                raise AdvisorError(
                    EXIT_CLAUDE,
                    "Claude analysis could not start",
                    outcome="claude_failed",
                    stderr_text=timeout_stderr,
                ) from exc
            if exc.reason == "io_error":
                raise AdvisorError(
                    EXIT_CLAUDE,
                    "Claude analysis I/O failed",
                    outcome="claude_failed",
                    stderr_text=timeout_stderr,
                ) from exc
            raise AdvisorError(
                EXIT_TIMEOUT,
                "Claude analysis timed out",
                outcome="timeout",
                stderr_text=timeout_stderr,
            ) from exc

        sanitized_stderr, redactions = redact(claude_stderr)
        atomic_write_text(stderr_path, sanitized_stderr)
        receipt["stderr_redactions"] = redactions
        receipt["claude_exit_code"] = claude_exit_code
        if claude_exit_code != 0:
            failure_path = run_dir / "claude-failure.json"
            failure_summary = summarize_failed_stream(
                claude_stdout, exit_code=claude_exit_code
            )
            atomic_write_json(failure_path, failure_summary)
            receipt["artifacts"]["claude_failure"] = str(failure_path)
            receipt["claude"]["models_observed"] = failure_summary["models_observed"]
            raise AdvisorError(
                EXIT_CLAUDE,
                "Claude analysis failed",
                outcome="claude_failed",
                stderr_text=sanitized_stderr,
            )
        events, envelope = parse_claude_stream(claude_stdout)

        response_path = run_dir / "claude-response.json"
        atomic_write_json(response_path, envelope)
        reported_turns = envelope.get("num_turns")
        reported_cost = envelope.get("total_cost_usd")
        turns_observed = (
            isinstance(reported_turns, int)
            and not isinstance(reported_turns, bool)
            and reported_turns >= 0
        )
        cost_observed = (
            isinstance(reported_cost, (int, float))
            and not isinstance(reported_cost, bool)
            and math.isfinite(reported_cost)
            and reported_cost >= 0
        )
        model_telemetry, model_issues = collect_model_telemetry(
            events, envelope, requested_family=limits["model"]
        )
        receipt["claude"].update(
            {
                "session_id": envelope.get("session_id"),
                "duration_ms": envelope.get("duration_ms"),
                "duration_api_ms": envelope.get("duration_api_ms"),
                "num_turns": reported_turns,
                "reported_cost_usd": reported_cost,
                "turn_enforcement_observed": turns_observed,
                "budget_enforcement_observed": cost_observed,
                **model_telemetry,
            }
        )
        receipt["artifacts"]["claude_response"] = str(response_path)
        if model_issues:
            receipt["claude"]["model_policy_violations"] = model_issues
            raise AdvisorError(
                EXIT_CLAUDE,
                "Claude model usage violated the selected quality profile",
                outcome="model_policy_violation",
            )
        if not turns_observed or not cost_observed:
            raise AdvisorError(
                EXIT_CLAUDE,
                "Claude did not report valid turn and cost usage",
                outcome="usage_unverified",
            )
        if reported_turns > limits["max_turns"]:
            raise AdvisorError(
                EXIT_CLAUDE,
                "Claude exceeded the requested turn ceiling",
                outcome="ceiling_breach",
            )
        if reported_cost > limits["max_budget_usd"]:
            raise AdvisorError(
                EXIT_CLAUDE,
                "Claude exceeded the requested cost ceiling",
                outcome="ceiling_breach",
            )
        result = extract_structured_output(envelope)
        validate_result(result, schema)
        result_path = run_dir / "result.json"
        report_path = run_dir / "report.md"
        atomic_write_json(result_path, result)
        report = (
            render_advisory(result) if kind == "advisory" else render_pr_review(result)
        )
        atomic_write_text(report_path, report)

        receipt["outcome"] = "success"
        receipt["result_sha256"] = sha256_text(compact_json(result))
        receipt["artifacts"] = {
            "request": str(request_path),
            "input_hash": str(input_hash_path),
            "claude_response": str(response_path),
            "result": str(result_path),
            "report": str(report_path),
            "stderr": str(stderr_path),
            "receipt": str(receipt_path),
        }
        return_payload = {
            "status": "success",
            "run_dir": str(run_dir),
            "result_path": str(result_path),
            "report_path": str(report_path),
            "receipt_path": str(receipt_path),
        }
    except AdvisorError as exc:
        receipt["outcome"] = exc.outcome
        receipt["error_code"] = exc.code
        receipt["error"] = exc.public_message
        exc.payload.update({"run_dir": str(run_dir), "receipt_path": str(receipt_path)})
        raise
    except Exception as exc:
        receipt["outcome"] = "internal_error"
        receipt["error_code"] = EXIT_INTERNAL
        receipt["error"] = "unexpected internal error"
        raise AdvisorError(
            EXIT_INTERNAL,
            "unexpected internal error",
            outcome="internal_error",
            payload={"run_dir": str(run_dir), "receipt_path": str(receipt_path)},
        ) from exc
    finally:
        receipt["finished_at"] = utc_now()
        receipt["duration_ms"] = round((time.monotonic() - start_monotonic) * 1000)
        try:
            atomic_write_json(receipt_path, receipt)
        except OSError:
            pass

    return return_payload


def read_context_files(
    paths: list[str],
    *,
    initial_bytes: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    if len(paths) > MAX_CONTEXT_FILES:
        raise AdvisorError(
            EXIT_USAGE,
            f"at most {MAX_CONTEXT_FILES} context files are allowed",
            outcome="rejected",
        )
    payload_items: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    source_paths: list[str] = []
    total_bytes = initial_bytes
    for index, raw_path in enumerate(paths, start=1):
        text, info = read_bounded_file(
            raw_path,
            label=f"context-{index}",
            max_bytes=max(0, MAX_INPUT_BYTES - total_bytes),
        )
        total_bytes += info["bytes"]
        payload_items.append(
            {"id": f"context-{index}", "path": info["path"], "content": text}
        )
        metadata.append(info)
        source_paths.append(raw_path)
    return payload_items, metadata, source_paths


def run_advisory(args: argparse.Namespace) -> dict[str, Any]:
    limits = validate_common_options(
        args,
        profiles=ADVISORY_PROFILE_DEFAULTS,
    )
    question_path: str | None = None
    if args.question_file:
        question, question_info = read_bounded_file(
            args.question_file, label="question"
        )
        question_path = args.question_file
    else:
        question = args.question
        raw_question = question.encode("utf-8")
        if len(raw_question) > MAX_SINGLE_FILE_BYTES:
            raise AdvisorError(
                EXIT_USAGE, "question exceeds the byte limit", outcome="rejected"
            )
        question_info = {
            "label": "question",
            "bytes": len(raw_question),
            "sha256": sha256_bytes(raw_question),
        }

    context_payload, context_metadata, source_paths = read_context_files(
        args.context_file,
        initial_bytes=question_info["bytes"],
    )
    if question_path:
        source_paths.append(question_path)
    payload = {"question": question, "context": context_payload}
    assembled_for_scan = "\n".join(
        [question, *(item["content"] for item in context_payload)]
    )
    findings = scan_sensitive(assembled_for_scan, source_paths)
    if findings and not args.allow_sensitive_input:
        raise AdvisorError(
            EXIT_USAGE,
            "sensitive input rejected; inspect the source or use --allow-sensitive-input explicitly",
            outcome="rejected",
        )
    preflight = doctor(require_gh=False)
    request = {
        "kind": "advisory",
        "question": question_info,
        "context": context_metadata,
        "limits": limits,
        "sensitive_input_override": args.allow_sensitive_input,
    }
    source = {
        "type": "advisory",
        "question_sha256": question_info["sha256"],
        "context_count": len(context_metadata),
    }
    return execute_claude(
        kind="advisory",
        prompt_name="advisory-prompt.md",
        schema_name="advisory-schema.json",
        payload=payload,
        request=request,
        source=source,
        limits=limits,
        output_dir=args.output_dir,
        sensitive_override=args.allow_sensitive_input,
        sensitive_findings=findings,
        doctor_result=preflight,
    )


PR_FIELDS = (
    "number,title,url,author,baseRefName,headRefName,baseRefOid,headRefOid,"
    "additions,deletions,changedFiles"
)


def gh_command(
    gh: str, arguments: list[str], *, max_stdout_bytes: int = MAX_GH_METADATA_BYTES
) -> str:
    try:
        return_code, stdout, _ = run_bounded_process(
            [gh, *arguments],
            child_kind="github",
            input_bytes=None,
            timeout=60,
            max_stdout_bytes=max_stdout_bytes,
            max_stderr_bytes=MAX_CHILD_STDERR_BYTES,
        )
    except BoundedProcessError as exc:
        if exc.reason == "timeout":
            raise AdvisorError(
                EXIT_GITHUB, "GitHub read timed out", outcome="github_failed"
            ) from exc
        if exc.reason == "limit":
            raise AdvisorError(
                EXIT_GITHUB,
                f"GitHub {exc.stream_name} exceeded the byte limit",
                outcome="github_failed",
            ) from exc
        if exc.reason == "io_error":
            raise AdvisorError(
                EXIT_GITHUB, "GitHub process I/O failed", outcome="github_failed"
            ) from exc
        raise AdvisorError(
            EXIT_GITHUB, "GitHub read failed", outcome="github_failed"
        ) from exc
    if return_code != 0:
        raise AdvisorError(EXIT_GITHUB, "GitHub read failed", outcome="github_failed")
    try:
        return stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AdvisorError(
            EXIT_GITHUB, "GitHub output is not valid UTF-8", outcome="github_failed"
        ) from exc


def get_update_status(gh: str) -> dict[str, Any]:
    raw = gh_command(
        gh,
        [
            "api",
            "--hostname",
            "github.com",
            UPDATE_ENDPOINT,
            "--method",
            "GET",
            "--header",
            "Accept: application/vnd.github+json",
        ],
    )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdvisorError(
            EXIT_GITHUB,
            "GitHub returned malformed release metadata",
            outcome="github_failed",
        ) from exc

    if not isinstance(payload, dict):
        raise AdvisorError(
            EXIT_GITHUB,
            "GitHub returned malformed release metadata",
            outcome="github_failed",
        )
    tag = payload.get("tag_name")
    release_url = payload.get("html_url")
    match = STABLE_RELEASE_TAG_PATTERN.fullmatch(tag) if isinstance(tag, str) else None
    expected_url = (
        f"https://github.com/{UPDATE_REPOSITORY}/releases/tag/{tag}" if match else None
    )
    if (
        match is None
        or release_url != expected_url
        or payload.get("draft") is not False
        or payload.get("prerelease") is not False
    ):
        raise AdvisorError(
            EXIT_GITHUB,
            "GitHub returned invalid or non-stable release metadata",
            outcome="github_failed",
        )

    installed_text = PLUGIN_VERSION.split("+", 1)[0]
    installed_match = STABLE_RELEASE_TAG_PATTERN.fullmatch(f"v{installed_text}")
    if installed_match is None:
        raise AdvisorError(
            EXIT_INTERNAL,
            "installed plugin version is not stable semantic versioning",
            outcome="internal_error",
        )
    installed = tuple(int(part) for part in installed_match.groups())
    latest = tuple(int(part) for part in match.groups())

    return {
        "checked": True,
        "channel": "github_releases",
        "repository": UPDATE_REPOSITORY,
        "installed_version": installed_text,
        "latest_version": tag.removeprefix("v"),
        "update_available": installed < latest,
        "ahead_of_latest": installed > latest,
        "release_url": release_url,
        "git_marketplace_update_command": GIT_MARKETPLACE_UPDATE_COMMAND,
        "new_task_required": True,
    }


def get_pr_metadata(gh: str, repository: str, number: int) -> dict[str, Any]:
    raw = gh_command(
        gh, ["pr", "view", str(number), "--repo", repository, "--json", PR_FIELDS]
    )
    try:
        metadata = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AdvisorError(
            EXIT_GITHUB,
            "GitHub returned malformed PR metadata",
            outcome="github_failed",
        ) from exc
    required = {
        "number",
        "baseRefOid",
        "headRefOid",
        "baseRefName",
        "headRefName",
        "title",
        "url",
    }
    if not isinstance(metadata, dict) or not required.issubset(metadata):
        raise AdvisorError(
            EXIT_GITHUB, "GitHub PR metadata is incomplete", outcome="github_failed"
        )
    return metadata


def capture_pr(
    doctor_result: dict[str, Any], repository: str, number: int
) -> tuple[dict[str, Any], str]:
    gh = doctor_result["github"]["path"]
    before = get_pr_metadata(gh, repository, number)
    diff = gh_command(
        gh,
        ["pr", "diff", str(number), "--repo", repository],
        max_stdout_bytes=MAX_SINGLE_FILE_BYTES,
    )
    after = get_pr_metadata(gh, repository, number)
    if (
        before["headRefOid"] != after["headRefOid"]
        or before["baseRefOid"] != after["baseRefOid"]
    ):
        raise AdvisorError(
            EXIT_GITHUB,
            "PR base or head changed while the review snapshot was captured; retry",
            outcome="github_changed",
        )
    return before, diff


def run_pr_review(args: argparse.Namespace) -> dict[str, Any]:
    limits = validate_common_options(args, profiles=PR_PROFILE_DEFAULTS)
    context_payload, context_metadata, source_paths = read_context_files(
        args.context_file,
        initial_bytes=0,
    )

    if args.pr is not None:
        if args.pr < 1:
            raise AdvisorError(
                EXIT_USAGE, "PR number must be positive", outcome="rejected"
            )
        if not args.repo or not REPOSITORY_PATTERN.fullmatch(args.repo):
            raise AdvisorError(
                EXIT_USAGE,
                "--repo OWNER/REPO is required for PR mode",
                outcome="rejected",
            )
        if args.source_label:
            raise AdvisorError(
                EXIT_USAGE,
                "--source-label is only valid with --diff-file",
                outcome="rejected",
            )
        preflight = doctor(require_gh=True)
        metadata, diff = capture_pr(preflight, args.repo, args.pr)
        source = {
            "type": "github_pr",
            "repository": args.repo,
            "pr_number": metadata["number"],
            "url": metadata["url"],
            "base_ref": metadata["baseRefName"],
            "head_ref": metadata["headRefName"],
            "base_oid": metadata["baseRefOid"],
            "head_oid": metadata["headRefOid"],
            "diff_semantics": "GitHub PR unified diff endpoint",
            "diff_sha256": sha256_text(diff),
            "diff_bytes": len(diff.encode("utf-8")),
        }
        public_metadata = {
            "number": metadata["number"],
            "title": metadata["title"],
            "url": metadata["url"],
            "author": metadata.get("author", {}).get("login")
            if isinstance(metadata.get("author"), dict)
            else None,
            "base_ref": metadata["baseRefName"],
            "head_ref": metadata["headRefName"],
            "base_oid": metadata["baseRefOid"],
            "head_oid": metadata["headRefOid"],
            "additions": metadata.get("additions"),
            "deletions": metadata.get("deletions"),
            "changed_files": metadata.get("changedFiles"),
        }
    else:
        if args.repo:
            raise AdvisorError(
                EXIT_USAGE, "--repo is only valid with --pr", outcome="rejected"
            )
        if not args.source_label:
            raise AdvisorError(
                EXIT_USAGE,
                "--source-label is required with --diff-file",
                outcome="rejected",
            )
        diff, diff_info = read_bounded_file(args.diff_file, label="diff")
        source_paths.append(args.diff_file)
        preflight = doctor(require_gh=False)
        source = {
            "type": "supplied_diff",
            "label": args.source_label,
            "diff_sha256": diff_info["sha256"],
            "diff_bytes": diff_info["bytes"],
        }
        public_metadata = {"source_label": args.source_label}

    payload = {
        "review_source": source,
        "metadata": public_metadata,
        "diff": diff,
        "context": context_payload,
    }
    scan_text = "\n".join(
        [
            diff,
            compact_json(source),
            compact_json(public_metadata),
            *(item["content"] for item in context_payload),
        ]
    )
    findings = scan_sensitive(scan_text, source_paths)
    if findings and not args.allow_sensitive_input:
        raise AdvisorError(
            EXIT_USAGE,
            "sensitive input rejected; inspect the source or use --allow-sensitive-input explicitly",
            outcome="rejected",
        )
    request = {
        "kind": "pr-review",
        "source": source,
        "context": context_metadata,
        "limits": limits,
        "critical": limits["quality_profile"] == "critical",
        "sensitive_input_override": args.allow_sensitive_input,
    }
    return execute_claude(
        kind="pr-review",
        prompt_name="pr-review-prompt.md",
        schema_name="pr-review-schema.json",
        payload=payload,
        request=request,
        source=source,
        limits=limits,
        output_dir=args.output_dir,
        sensitive_override=args.allow_sensitive_input,
        sensitive_findings=findings,
        doctor_result=preflight,
    )


def add_common_analysis_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--context-file", action="append", default=[], metavar="PATH")
    parser.add_argument("--output-dir", metavar="PATH")
    quality = parser.add_mutually_exclusive_group()
    quality.add_argument("--quality", choices=QUALITY_PROFILES)
    quality.add_argument(
        "--critical", dest="quality", action="store_const", const="critical"
    )
    parser.add_argument("--acknowledge-standard-quality", action="store_true")
    parser.add_argument("--max-turns", type=int)
    parser.add_argument("--max-budget-usd", type=float)
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--allow-sensitive-input", action="store_true")


def build_parser() -> SafeArgumentParser:
    parser = SafeArgumentParser(prog="amanerp-second-opinion", description=__doc__)
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {PLUGIN_VERSION}"
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=SafeArgumentParser
    )

    doctor_parser = subparsers.add_parser(
        "doctor", help="Verify local prerequisites without exposing credentials"
    )
    doctor_parser.add_argument("--require-gh", action="store_true")
    doctor_parser.add_argument(
        "--check-update",
        action="store_true",
        help="explicitly check the latest stable GitHub release without installing it",
    )

    advisory = subparsers.add_parser(
        "advisory", help="Ask Claude for a bounded independent advisory"
    )
    question_group = advisory.add_mutually_exclusive_group(required=True)
    question_group.add_argument("--question")
    question_group.add_argument("--question-file", metavar="PATH")
    add_common_analysis_options(advisory)

    pr_review = subparsers.add_parser(
        "pr-review", help="Ask Claude for an independent PR or diff review"
    )
    source_group = pr_review.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--pr", type=int)
    source_group.add_argument("--diff-file", metavar="PATH")
    pr_review.add_argument("--repo", metavar="OWNER/REPO")
    pr_review.add_argument("--source-label")
    add_common_analysis_options(pr_review)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.command == "doctor":
            emit(
                doctor(
                    require_gh=args.require_gh or args.check_update,
                    check_update=args.check_update,
                )
            )
            return 0
        if args.command == "advisory":
            emit(run_advisory(args))
            return 0
        if args.command == "pr-review":
            emit(run_pr_review(args))
            return 0
        raise AdvisorError(EXIT_USAGE, "a command is required", outcome="rejected")
    except AdvisorError as exc:
        diagnostic(exc.public_message)
        emit(
            {
                "status": "error",
                "code": exc.code,
                "message": exc.public_message,
                **exc.payload,
            }
        )
        return exc.code
    except KeyboardInterrupt:
        diagnostic("interrupted")
        emit({"status": "error", "code": EXIT_INTERNAL, "message": "interrupted"})
        return EXIT_INTERNAL
    except Exception:
        diagnostic("unexpected internal error")
        emit(
            {
                "status": "error",
                "code": EXIT_INTERNAL,
                "message": "unexpected internal error",
            }
        )
        return EXIT_INTERNAL


if __name__ == "__main__":
    raise SystemExit(main())
