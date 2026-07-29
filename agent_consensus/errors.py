"""Public exceptions raised by :mod:`agent_consensus`."""


class ConsensusError(Exception):
    """Base class for package-specific errors."""


class ConfigurationError(ConsensusError, ValueError):
    """Raised when engine or voting configuration is invalid."""


class DuplicateParticipantError(ConfigurationError):
    """Raised when more than one participant uses the same name."""


class ResponseValidationError(ConsensusError, ValueError):
    """Raised when a participant response violates the response contract."""
