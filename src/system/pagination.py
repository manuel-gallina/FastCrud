from pydantic import AliasChoices, BaseModel, Field, create_model


class PaginationParams(BaseModel):
    skip: int
    limit: int


_pagination_models_cache: dict[str, type[PaginationParams]] = {}


def get_pagination(
    default_limit: int | None = 50, max_limit: int | None = 200
) -> type[PaginationParams]:
    """
    Returns an object with the pagination parameters.

    This method creates a new Pydantic model for validating pagination parameters with the specified default and maximum limits.
    :param default_limit:
    :param max_limit:
    :return: A Pydantic model for pagination parameters.
    """
    global _pagination_models_cache

    key = f"{default_limit}-{max_limit}"
    if key in _pagination_models_cache:
        return _pagination_models_cache[key]

    skip = Field(0, ge=0, validation_alias=AliasChoices("skip", "offset"))

    limit_validation_aliases = AliasChoices("limit", "take")
    if default_limit is not None and max_limit is not None:
        limit = Field(
            default_limit,
            ge=1,
            le=max_limit,
            validation_alias=limit_validation_aliases,
        )
    elif default_limit is not None:
        limit = Field(default_limit, validation_alias=limit_validation_aliases)
    elif max_limit is not None:
        limit = Field(..., le=max_limit, validation_alias=limit_validation_aliases)
    else:
        limit = Field(..., validation_alias=limit_validation_aliases)

    model = create_model(
        "DynamicPaginationParams",
        __base__=PaginationParams,
        skip=(int, skip),
        limit=(int, limit),
    )

    _pagination_models_cache[key] = model

    return model
