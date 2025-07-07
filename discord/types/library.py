from __future__ import annotations
from typing import List, TypedDict
from typing_extensions import NotRequired
from .application import Branch, PartialApplication
from .entitlements import Entitlement
from .snowflake import Snowflake
from .store import PartialSKU
class LibraryApplication(TypedDict):
    created_at: str
    application: PartialApplication
    sku_id: Snowflake
    sku: PartialSKU
    entitlements: List[Entitlement]
    flags: int
    branch_id: Snowflake
    branch: NotRequired[Branch]