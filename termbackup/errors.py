"""
Custom exception hierarchy for TermBackup.
"""

class TermBackupError(Exception):
    """Base exception for all termbackup errors."""
    pass

class CryptoError(TermBackupError):
    pass

class KeyDerivationError(CryptoError):
    pass

class EncryptionError(CryptoError):
    pass

class DecryptionError(CryptoError):
    pass

class SignatureError(CryptoError):
    pass

class SnapshotError(TermBackupError):
    pass

class SnapshotCreationError(SnapshotError):
    pass

class SnapshotCorruptedError(SnapshotError):
    pass

class RestoreError(TermBackupError):
    pass

class RestoreExtractionError(RestoreError):
    pass

class PathTraversalError(RestoreError):
    pass

class GitHubError(TermBackupError):
    pass

class AuthenticationError(GitHubError):
    pass

class RateLimitError(GitHubError):
    pass

class UploadError(GitHubError):
    pass

class ConfigError(TermBackupError):
    pass

class ProfileNotFoundError(ConfigError):
    pass

class ProfileValidationError(ConfigError):
    pass

class PluginError(TermBackupError):
    pass

class PluginLoadError(PluginError):
    pass

class PluginSandboxViolation(PluginError):
    pass

class ManifestError(TermBackupError):
    pass

class DaemonError(TermBackupError):
    pass
