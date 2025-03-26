from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field, AliasChoices, Json

from system.query_builder import (
    WhereRule,
)


class FilteringParams(BaseModel):
    where: Json[WhereRule] | None = Field(
        None, validation_alias=AliasChoices("where", "filters")
    )


def get_filtering(filtering: Annotated[FilteringParams, Query()]) -> FilteringParams:
    return filtering
