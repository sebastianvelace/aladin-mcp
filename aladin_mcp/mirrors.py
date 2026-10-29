"""Try a list of mirrors in order, remembering the last one that worked."""

from typing import Callable, TypeVar

T = TypeVar("T")


class ServiceUnavailable(RuntimeError):
    """Every mirror of a service failed."""


class MirrorPool:
    def __init__(self, label: str, servers: list[str]):
        self.label = label
        self._servers = list(servers)

    def run(self, fn: Callable[[str], T]) -> tuple[T, str]:
        errors = []
        for server in list(self._servers):
            try:
                result = fn(server)
            except Exception as exc:  # network errors come in many types
                errors.append(f"- {server}: {describe_error(exc)}")
                continue
            # Promote the working mirror so the next call does not wait on a dead one.
            self._servers.remove(server)
            self._servers.insert(0, server)
            return result, server
        raise ServiceUnavailable(
            f"{self.label}: no mirror answered.\n" + "\n".join(errors) +
            "\nThe CDS services may be down or slow, or your network may be "
            "blocking them. Try again in a few minutes or raise ALADIN_MCP_TIMEOUT."
        )


def describe_error(exc: Exception) -> str:
    text = str(exc)
    name = type(exc).__name__
    if "timed out" in text.lower() or "timeout" in name.lower():
        return "timeout (no response)"
    if "504" in text or "502" in text or "503" in text:
        return f"server error ({text.split(' for url')[0][:80]})"
    if "connection" in text.lower():
        return "could not connect"
    return f"{name}: {text[:160]}"
