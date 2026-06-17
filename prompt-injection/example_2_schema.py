"""
Layer 2: Strict Output Schema Enforcement (Pydantic v2)
Author: Stefan Miladinovic - DigitalBricks (https://digitalbricks.ai/)

Forces LLM tool-call arguments through Pydantic validation.
Wrong table, SQL in a field name, shell commands in a value -- all rejected.
"""

import json
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


# Only these tables and fields are allowed -- everything else is rejected
class AllowedTable(str, Enum):
    CUSTOMERS = "customers"
    ORDERS = "orders"
    PRODUCTS = "products"


class AllowedPatchField(str, Enum):
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"


# Pydantic schemas for each tool -- validators catch hidden SQL/shell injection
class DatabaseLookupArgs(BaseModel):
    # table MUST be one of the enum values -- "admin_secrets" would fail
    table: AllowedTable
    # record_id can only be letters, numbers, hyphens, underscores
    record_id: str = Field(pattern=r"^[A-Za-z0-9\-_]+$", max_length=64)
    fields: list[str] = ["*"]

    @field_validator("fields", mode="before")
    @classmethod
    def block_sql_in_fields(cls, v: list[str]) -> list[str]:
        """Catch things like: fields=["email; DROP TABLE users--"]"""
        bad = re.compile(r"(drop|delete|truncate|--|;)", re.I)
        for f in v:
            if bad.search(f):
                raise ValueError(f"SQL keyword in field name: '{f}'")
        return v


class RecordPatchArgs(BaseModel):
    table: AllowedTable
    record_id: str = Field(pattern=r"^[A-Za-z0-9\-_]+$", max_length=64)
    # field MUST be one of the enum values -- "password_hash" would fail
    field: AllowedPatchField
    new_value: str = Field(max_length=256)

    @field_validator("new_value")
    @classmethod
    def block_injection_in_value(cls, v: str) -> str:
        """Catch things like: new_value="legit@mail.com; rm -rf /" """
        bad = re.compile(r"(;|\||&&|`|\$\(|drop\s|rm\s+-rf|sudo)", re.I)
        if bad.search(v):
            raise ValueError(f"Injection pattern in value: '{v[:40]}'")
        return v


# Map tool names to their schema -- unknown tools get rejected automatically
TOOL_SCHEMAS: dict[str, type[BaseModel]] = {
    "database_lookup": DatabaseLookupArgs,
    "patch_record": RecordPatchArgs,
}


# Validation gate: sits between LLM output and actual tool execution
def validate_tool_call(tool_name: str, raw_args: dict[str, Any]) -> dict | None:
    """Returns validated args dict if OK, None if rejected."""

    schema = TOOL_SCHEMAS.get(tool_name)
    if not schema:
        print(f"  REJECTED: unknown tool '{tool_name}'")
        return None

    try:
        validated = schema.model_validate(raw_args)
        print(f"  VALID: {validated.model_dump()}")
        return validated.model_dump()
    except ValidationError as e:
        print(f"  REJECTED: {e.error_count()} error(s)")
        for err in e.errors():
            print(f"    - {err['loc']}: {err['msg']}")
        return None


# Try it out
if __name__ == "__main__":

    tests = [
        # These should PASS
        ("valid lookup", "database_lookup",
         {"table": "customers", "record_id": "C-1042", "fields": ["email"]}),

        ("valid patch", "patch_record",
         {"table": "orders", "record_id": "ORD-88", "field": "address",
          "new_value": "742 Evergreen Terrace"}),

        # These should all be REJECTED
        ("SQL in fields", "database_lookup",
         {"table": "customers", "record_id": "C-1042",
          "fields": ["email; DROP TABLE customers--"]}),

        ("bad table", "database_lookup",
         {"table": "admin_secrets", "record_id": "ROOT", "fields": ["*"]}),

        ("shell in value", "patch_record",
         {"table": "customers", "record_id": "C-1042", "field": "email",
          "new_value": "x@test.com; rm -rf /"}),

        ("bad field", "patch_record",
         {"table": "customers", "record_id": "C-1042",
          "field": "password_hash", "new_value": "pwned"}),

        ("unknown tool", "execute_raw_sql",
         {"query": "DROP TABLE customers;"}),
    ]

    for label, tool, args in tests:
        print(f"\n[{label.upper()}] {tool}({json.dumps(args)})")
        result = validate_tool_call(tool, args)
        if result:
            print("  -> Would execute tool here.")
