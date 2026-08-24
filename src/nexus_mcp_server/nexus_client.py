import asyncio
from typing import Any, AsyncGenerator, Dict, Optional

import httpx

from .errors import (
    NexusApiError,
    NexusAuthError,
    NexusNotFoundError,
    NexusPermissionError,
    NexusRateLimitError,
    NexusServerError,
    SafetyError,
)
from .logging import get_logger
from .safety import redact_secrets

logger = get_logger("client")

class NexusClient:
    """Async client for Nexus Repository Manager."""

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        verify_tls: bool = True,
        timeout: int = 30,
        allowed_hosts: Optional[list[str]] = None,
        max_response_bytes: int = 1048576,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_tls = verify_tls
        self.timeout = timeout
        self.allowed_hosts = allowed_hosts
        self.max_response_bytes = max_response_bytes

        self._validate_host(self.base_url)

        # Prepare auth
        self.auth: Optional[httpx.BasicAuth] = None
        if self.username and self.password:
            self.auth = httpx.BasicAuth(self.username, self.password)

        self._client: Optional[httpx.AsyncClient] = None

    def _validate_host(self, url: str) -> None:
        """Validate that the host is allowed."""
        if not self.allowed_hosts:
            return

        from urllib.parse import urlparse
        hostname = urlparse(url).hostname
        if not hostname:
            raise SafetyError(f"Invalid URL: {url}")

        if hostname not in self.allowed_hosts:
            raise SafetyError(f"Access to host {hostname} is not allowed by NEXUS_ALLOWED_HOSTS.")

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=self.auth,
                verify=self.verify_tls,
                timeout=self.timeout,
                follow_redirects=True,
                trust_env=False,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> Any:
        """Execute a request with retries and error handling."""
        client = await self.get_client()
        if path.startswith(("http://", "https://")):
            raise SafetyError("Absolute request URLs are not allowed; use paths relative to the configured Nexus URL.")
        url = f"{self.base_url}{path}"

        last_exception = None
        for attempt in range(retries + 1):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                )

                # Check for transient errors to retry
                if response.status_code in (429, 502, 503, 504):
                    if attempt < retries:
                        wait = backoff_factor * (2 ** attempt)
                        logger.warning(f"Transient error {response.status_code} for {method} {path}. Retrying in {wait:.2f}s...")
                        await asyncio.sleep(wait)
                        continue

                return self._handle_response(response)

            except httpx.HTTPError as e:
                last_exception = e
                if attempt < retries:
                    wait = backoff_factor * (2 ** attempt)
                    logger.warning(f"HTTP error {e} for {method} {path}. Retrying in {wait:.2f}s...")
                    await asyncio.sleep(wait)
                    continue
                break

        raise NexusApiError(f"Request failed after {retries} retries: {last_exception}")

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle HTTP response and map to custom errors."""
        # Check size
        if len(response.content) > self.max_response_bytes:
            raise SafetyError(f"Response size ({len(response.content)} bytes) exceeds limit ({self.max_response_bytes}).")

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            status = response.status_code
            text = response.text
            try:
                details = redact_secrets(response.json(), [self.password] if self.password else [])
            except Exception:
                details = redact_secrets({"raw": text}, [self.password] if self.password else [])

            if status == 401:
                raise NexusAuthError("Authentication failed", status, details)
            elif status == 403:
                raise NexusPermissionError("Permission denied", status, details)
            elif status == 404:
                raise NexusNotFoundError("Resource not found", status, details)
            elif status == 429:
                raise NexusRateLimitError("Rate limit exceeded", status, details)
            elif status >= 500:
                raise NexusServerError(f"Server error: {status}", status, details)
            else:
                raise NexusApiError(f"API error: {status}", status, details)

        if response.status_code == 204:
            return None

        try:
            return response.json()
        except Exception:
            return response.text

    async def list_paginated(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = 10,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generator for paginated Nexus endpoints using continuationToken."""
        params = params.copy() if params else {}
        pages_fetched = 0

        while pages_fetched < max_pages:
            data = await self.request("GET", path, params=params)

            if not isinstance(data, dict):
                logger.error(f"Expected dict for paginated response, got {type(data)}")
                break

            items = data.get("items", [])
            for item in items:
                yield item

            token = data.get("continuationToken")
            if not token:
                break

            params["continuationToken"] = token
            pages_fetched += 1

    async def get_all(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        max_items: int = 1000,
    ) -> list[Dict[str, Any]]:
        """Collect all items from a paginated endpoint."""
        results = []
        async for item in self.list_paginated(path, params):
            results.append(item)
            if len(results) >= max_items:
                break
        return results
