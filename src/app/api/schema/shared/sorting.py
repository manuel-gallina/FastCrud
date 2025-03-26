from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, Field, AliasChoices, Json

from system.query_builder import (
    OrderByRule,
)


class SortingParams(BaseModel):
    order_by: Json[list[OrderByRule]] | None = Field(
        None, validation_alias=AliasChoices("orderBy", "sort")
    )


def get_sorting(sorting: Annotated[SortingParams, Query()]) -> SortingParams:
    return sorting
