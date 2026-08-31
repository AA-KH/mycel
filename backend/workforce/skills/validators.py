from core.errors import DomainError

def validate_proficiency_baseline(level: int) -> None:
    if not isinstance(level, int):
        raise DomainError("Proficiency baseline must be an integer")
    if not (0 <= level <= 100):
        raise DomainError("Proficiency baseline must be between 0 and 100")
