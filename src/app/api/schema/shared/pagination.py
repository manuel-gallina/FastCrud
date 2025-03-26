from pydantic import Field, AliasChoices, create_model, BaseModel, AliasPath


class PaginationParams(BaseModel):
    skip: int
    limit: int


_pagination_models_cache: dict[str, type[BaseModel]] = {}


def _build_limit_field(
    default_limit: int | None,
    max_limit: int | None,
    validation_alias: str | AliasPath | AliasChoices | None,
) -> Field:
    if default_limit is not None and max_limit is not None:
        limit = Field(
            default_limit,
            ge=1,
            le=max_limit,
            validation_alias=validation_alias,
        )
    elif default_limit is not None:
        limit = Field(default_limit, validation_alias=validation_alias)
    elif max_limit is not None:
        limit = Field(..., le=max_limit, validation_alias=validation_alias)
    else:
        limit = Field(..., validation_alias=validation_alias)

    return limit


def get_pagination(
    default_limit: int | None = 50, max_limit: int | None = 200
) -> type[BaseModel]:
    """
    Create a new Pydantic model for validating pagination parameters with the specified default and maximum limits.
    :param default_limit:
    :param max_limit:
    :return:
    """
    global _pagination_models_cache

    key = f"{default_limit}-{max_limit}"
    if key in _pagination_models_cache:
        return _pagination_models_cache[key]

    skip = Field(0, ge=0, validation_alias=AliasChoices("skip", "offset"))
    limit = _build_limit_field(default_limit, max_limit, AliasChoices("limit", "take"))

    model = create_model(
        "DynamicPaginationParams", skip=(int, skip), limit=(int, limit)
    )

    _pagination_models_cache[key] = model

    return model
