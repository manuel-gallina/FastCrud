from abc import abstractmethod
from uuid import UUID

from sqlalchemy import Select
from starlette import status

from app.api.schema.shared.base import BaseSchema
from app.api.schema.shared.errors import ApiError
from system.query_builder import (
    Field,
    WhereRule,
    OrderByRule,
    EngineContext,
    QueryBuilderSyntaxError,
)


class BaseEntitySchema(BaseSchema):
    id: UUID

    @staticmethod
    @abstractmethod
    def get_query_builder_fields() -> list[Field]:
        raise NotImplementedError()

    @classmethod
    def build_query(
        cls,
        base_query: Select,
        skip: int | None = None,
        limit: int | None = None,
        where: WhereRule | None = None,
        order_by: list[OrderByRule] | None = None,
    ) -> Select:
        try:
            engine_context = EngineContext(cls.get_query_builder_fields())

            if skip:
                base_query = base_query.offset(skip)
            if limit:
                base_query = base_query.limit(limit)
            if where:
                compiled_where = where.compile(engine_context)
                base_query = base_query.where(compiled_where)
            if order_by:
                compiled_order_by = [rule.compile(engine_context) for rule in order_by]
                base_query = base_query.order_by(*compiled_order_by)

            base_query = base_query.params(engine_context.params)

            return base_query
        except QueryBuilderSyntaxError as e:
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Invalid query builder syntax",
                detail=str(e),
            )
