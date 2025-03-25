"""
Common type definitions for the application.
"""
from typing import Dict, Mapping, TypeAlias

ModelTokenLimits: TypeAlias = Dict[str, int]
TokenLimitsMapping: TypeAlias = Mapping[str, int] 