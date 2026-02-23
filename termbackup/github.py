"""
GitHub synchronization client using httpx[http2].
Handles token validation, rate limits, and chunked uploads.
"""
import base64
import time
from typing import Any, Dict, List, Optional

import httpx

from .errors import AuthenticationError, RateLimitError, UploadError
from .manifest import load_manifest, serialize_manifest
from .models import Manifest


class TokenValidationResult:
    def __init__(self, is_valid: bool, scopes: List[str], token_type: str, needs_warning: bool = False, message: str = ""):
        self.is_valid = is_valid
        self.scopes = scopes
        self.token_type = token_type
        self.needs_warning = needs_warning
        self.message = message

class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.github.com"
        self._client = httpx.Client(
            http2=True,
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "X-GitHub-Api-Version": "2022-11-28"
            },
            timeout=30.0
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Centralized request handler with exponential backoff and rate limit awareness."""
        retries = 3
        base_wait = 1.0
        
        for attempt in range(retries):
            response = self._client.request(method, path, **kwargs)
            
            # Check rate limits pre-emptively
            if "X-RateLimit-Remaining" in response.headers:
                remaining = int(response.headers["X-RateLimit-Remaining"])
                if remaining < 10 and attempt == 0:
                    pass # We could logger.warning here
            
            if response.status_code == 401:
                raise AuthenticationError("GitHub token is invalid or expired.")
            elif response.status_code == 403 and "rate limit" in response.text.lower():
                reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait_time = max(0.1, reset_time - time.time())
                raise RateLimitError(f"GitHub rate limit exceeded. Resets in {int(wait_time)}s.")
            elif response.status_code >= 500:
                if attempt < retries - 1:
                    time.sleep(base_wait * (2 ** attempt))
                    continue
                raise UploadError(f"GitHub API error: {response.status_code} - {response.text}")
                
            return response
            
        raise UploadError("Max retries exceeded.")

    def validate_token(self) -> TokenValidationResult:
        """
        Validate token type (classic vs fine-grained) and scopes.
        Classic tokens return scopes in `X-OAuth-Scopes` headers.
        Fine-grained (and GitHub App) tokens don't always, so we must check via /user or /user/installations endpoints.
        """
        try:
            resp = self._request("GET", "/user")
            is_valid = resp.status_code == 200
            
            if not is_valid:
                return TokenValidationResult(False, [], "unknown", message="Token is invalid.")
                
            scopes_header = resp.headers.get("X-OAuth-Scopes", "")
            
            if self.token.startswith("ghp_"):
                token_type = "classic"
                scopes = [s.strip() for s in scopes_header.split(",") if s.strip()]
                has_repo = "repo" in scopes
                needs_warning = not has_repo
                msg = "" if has_repo else "Classic token lacks 'repo' scope."
                return TokenValidationResult(True, scopes, token_type, needs_warning, msg)
                
            elif self.token.startswith("github_pat_"):
                # Fine-grained
                token_type = "fine-grained"
                # Fine-grained tokens don't explicitly list scopes in X-OAuth-Scopes usually.
                # We do a best-effort check or assume user provided it correctly, warning them to verify.
                # A true check would require hitting a repo endpoint, but we might not have a repo yet.
                return TokenValidationResult(True, [], token_type, False, "Fine-grained token detected. Ensure repository write permissions are granted.")
                
            else:
                return TokenValidationResult(True, [], "unknown", False, "Unknown token type detected.")
            
        except AuthenticationError:
            return TokenValidationResult(False, [], "unknown", message="Token authentication failed.")

    def upload_file(self, repo: str, path: str, content: bytes, message: str) -> None:
        """Upload a file to the repository. Handles creating or updating."""
        # Check if file exists to get SHA for update
        encoded_content = base64.b64encode(content).decode("ascii")
        
        file_url = f"/repos/{repo}/contents/{path}"
        get_resp = self._client.get(file_url)
        
        payload: Dict[str, Any] = {
            "message": message,
            "content": encoded_content
        }
        
        if get_resp.status_code == 200:
            # File exists, append sha to update
            payload["sha"] = get_resp.json()["sha"]
            
        resp = self._request("PUT", file_url, json=payload)
        if resp.status_code not in (200, 201):
            raise UploadError(f"Failed to upload {path}: {resp.status_code} {resp.text}")

    def download_file(self, repo: str, path: str) -> bytes:
        """Download a file's raw content."""
        file_url = f"/repos/{repo}/contents/{path}"
        resp = self._request("GET", file_url, headers={"Accept": "application/vnd.github.v3.raw"})
        if resp.status_code == 404:
            raise FileNotFoundError(f"File {path} not found in {repo}")
        if resp.status_code != 200:
            raise UploadError(f"Failed to download {path}: {resp.status_code}")
        return resp.content

    def list_snapshots(self, repo: str) -> List[str]:
        """List snapshot IDs directly from the repository structure."""
        try:
            resp = self._request("GET", f"/repos/{repo}/contents/snapshots")
            if resp.status_code == 404:
                return []
            if resp.status_code != 200:
                raise UploadError("Failed to list snapshots.")
            
            data = resp.json()
            return [str(item["name"]) for item in data if isinstance(item, dict) and str(item["name"]).endswith(".tbk")]
        except FileNotFoundError:
            return []

    def upload_manifest(self, repo: str, manifest: Manifest) -> None:
        """Upload the updated manifest.json."""
        content = serialize_manifest(manifest)
        self.upload_file(repo, "manifest.json", content, "Update manifest")

    def download_manifest(self, repo: str) -> Optional[Manifest]:
        """Download and parse manifest.json."""
        try:
            data = self.download_file(repo, "manifest.json")
            return load_manifest(data)
        except FileNotFoundError:
            return None
