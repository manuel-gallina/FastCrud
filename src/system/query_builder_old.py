from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Union, Annotated, Literal, Optional, Callable

from pydantic import BaseModel, Field as PydanticField, Tag, Discriminator
from sqlmodel import bindparam, func, and_, or_, not_


class Field:
    name: str
    database_column: Any

    _transform_function: Optional[Callable]

    def __init__(
        self,
        name: str,
        database_column: Any,
        transform_function: Optional[Callable] = None,
    ):
        self.name = name
        self.database_column = database_column
        self._transform_function = transform_function

    def transform(self, value: Any) -> Any:
        if self._transform_function is None:
            return value

        if isinstance(value, list):
            transformed_value = [self._transform_function(v) for v in value]
        else:
            transformed_value = self._transform_function(value)
        return transformed_value


class QueryBuilderSyntaxError(Exception):
    pass


class QueryBuilderUnknownFieldError(QueryBuilderSyntaxError):
    def __init__(self, field_name: str):
        super().__init__(f"Unknown query builder field: {field_name}")


class EngineContext:
    params: dict
    param_counters: dict[str, int]
    fields: dict[str, Field]

    def __init__(self, fields: list[Field]):
        self.params = {}
        self.param_counters = {}
        self.fields = {field.name: field for field in fields}

    def add_param(self, field: Field, value: Any) -> str:
        param_counter = self.param_counters.get(field.name, 0)
        param_name = f"{field.name}_{param_counter}"
        self.params |= {param_name: value}
        self.param_counters |= {field.name: param_counter + 1}
        return param_name


class _IRule(BaseModel, ABC):
    @abstractmethod
    def compile(self, engine_context: EngineContext) -> Any:
        raise NotImplementedError()


class _Directions(str, Enum):
    ASC = "asc"
    DESC = "desc"


class _BaseOrderByRule(_IRule):
    field: str
    direction: _Directions = _Directions.ASC

    @abstractmethod
    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
    ):
        raise NotImplementedError()

    def compile(self, engine_context: EngineContext) -> Any:
        try:
            field = engine_context.fields[self.field]
        except KeyError as e:
            raise QueryBuilderUnknownFieldError(self.field) from e
        return self.apply(engine_context, field)


class Asc(_BaseOrderByRule):
    direction: Literal[_Directions.ASC] = _Directions.ASC

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
    ):
        return field.database_column


class Desc(_BaseOrderByRule):
    direction: Literal[_Directions.DESC] = _Directions.DESC

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
    ):
        return field.database_column.desc()


def _discriminate_direction(
    v: Any,
) -> str:
    if isinstance(v, dict):
        if "direction" in v:
            if v["direction"] not in _Directions:
                return "unknown"
            return v["direction"]
        return _Directions.ASC
    return v.direction


OrderByRule = Annotated[
    Union[
        Annotated[_BaseOrderByRule, Tag("unknown")],
        Annotated[Asc, Tag(_Directions.ASC)],
        Annotated[Desc, Tag(_Directions.DESC)],
    ],
    Discriminator(_discriminate_direction),
]


class _Operators(str, Enum):
    EQUAL = "equal"
    IEQUAL = "iequal"
    LIKE = "like"
    ILIKE = "ilike"
    NOTEQUAL = "notequal"
    INOTEQUAL = "inotequal"
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    IN = "in"
    NOTIN = "notin"
    GREATERTHAN = "greaterthan"
    GREATERTHANOREQUAL = "greaterthanorequal"
    LESSTHAN = "lessthan"
    LESSTHANOREQUAL = "lessthanorequal"
    ISNULL = "isnull"
    ISNOTNULL = "isnotnull"
    ISEMPTY = "isempty"
    ISNOTEMPTY = "isnotempty"
    STARTSWITH = "startswith"
    ISTARTSWITH = "istartswith"
    ENDSWITH = "endswith"
    IENDSWITH = "iendswith"
    ANY = "any"
    ALL = "all"

    def __repr__(self):
        return self.value


class _BaseSimpleWhereRule(_IRule):
    field: str
    operator: _Operators
    value: Any

    @abstractmethod
    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        raise NotImplementedError()

    def compile(self, engine_context: EngineContext) -> Any:
        try:
            field = engine_context.fields[self.field]
        except KeyError as e:
            raise QueryBuilderUnknownFieldError(self.field) from e
        transformed_value = field.transform(self.value)
        return self.apply(engine_context, field, transformed_value)


_Scalar = str | int | float | bool


class Equal(_BaseSimpleWhereRule):
    operator: Literal[_Operators.EQUAL] = _Operators.EQUAL
    value: _Scalar | list[_Scalar] | None

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column == bindparam(
            engine_context.add_param(field, value)
        )


class IEqual(Equal):
    operator: Literal[_Operators.IEQUAL] = _Operators.IEQUAL

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return func.lower(field.database_column) == func.lower(
            bindparam(engine_context.add_param(field, value))
        )


class Like(_BaseSimpleWhereRule):
    operator: Literal[_Operators.LIKE] = _Operators.LIKE
    value: str

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.like(
            bindparam(engine_context.add_param(field, value))
        )


class ILike(Like):
    operator: Literal[_Operators.ILIKE] = _Operators.ILIKE

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.ilike(
            bindparam(engine_context.add_param(field, value))
        )


class NotEqual(Equal):
    operator: Literal[_Operators.NOTEQUAL] = _Operators.NOTEQUAL

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column != bindparam(
            engine_context.add_param(field, value)
        )


class INotEquals(Equal):
    operator: Literal[_Operators.INOTEQUAL] = _Operators.INOTEQUAL

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return func.lower(field.database_column) != func.lower(
            bindparam(engine_context.add_param(field, value))
        )


class Contains(Like):
    operator: Literal[_Operators.CONTAINS] = _Operators.CONTAINS

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.like(
            bindparam(engine_context.add_param(field, f"%{value}%"))
        )


class IContains(Like):
    operator: Literal[_Operators.ICONTAINS] = _Operators.ICONTAINS

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.ilike(
            bindparam(engine_context.add_param(field, f"%{value}%"))
        )


class In(_BaseSimpleWhereRule):
    operator: Literal[_Operators.IN] = _Operators.IN
    value: list[_Scalar]

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.in_(tuple(value))


class NotIn(In):
    operator: Literal[_Operators.NOTIN] = _Operators.NOTIN

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.notin_(tuple(value))


class GreaterThan(Equal):
    operator: Literal[_Operators.GREATERTHAN] = _Operators.GREATERTHAN

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column > bindparam(engine_context.add_param(field, value))


class GreaterThanOrEqual(Equal):
    operator: Literal[_Operators.GREATERTHANOREQUAL] = _Operators.GREATERTHANOREQUAL

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column >= bindparam(
            engine_context.add_param(field, value)
        )


class LessThan(Equal):
    operator: Literal[_Operators.LESSTHAN] = _Operators.LESSTHAN

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column < bindparam(engine_context.add_param(field, value))


class LessThanOrEqual(Equal):
    operator: Literal[_Operators.LESSTHANOREQUAL] = _Operators.LESSTHANOREQUAL

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column <= bindparam(
            engine_context.add_param(field, value)
        )


class IsNull(_BaseSimpleWhereRule):
    operator: Literal[_Operators.ISNULL] = _Operators.ISNULL
    value: None

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.is_(None)


class IsNotNull(IsNull):
    operator: Literal[_Operators.ISNOTNULL] = _Operators.ISNOTNULL

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.is_not(None)


class IsEmpty(Like):
    operator: Literal[_Operators.ISEMPTY] = _Operators.ISEMPTY

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return func.trim(field.database_column) == ""


class IsNotEmpty(Like):
    operator: Literal[_Operators.ISNOTEMPTY] = _Operators.ISNOTEMPTY

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return func.trim(field.database_column) != ""


class StartsWith(Like):
    operator: Literal[_Operators.STARTSWITH] = _Operators.STARTSWITH

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.like(
            bindparam(engine_context.add_param(field, f"{value}%"))
        )


class IStartsWith(Like):
    operator: Literal[_Operators.ISTARTSWITH] = _Operators.ISTARTSWITH

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.ilike(
            bindparam(engine_context.add_param(field, f"{value}%"))
        )


class EndsWith(Like):
    operator: Literal[_Operators.ENDSWITH] = _Operators.ENDSWITH

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.like(
            bindparam(engine_context.add_param(field, f"%{value}"))
        )


class IEndsWith(Like):
    operator: Literal[_Operators.IENDSWITH] = _Operators.IENDSWITH

    def apply(
        self,
        engine_context: EngineContext,
        field: Field,
        value: Any,
    ):
        return field.database_column.ilike(
            bindparam(engine_context.add_param(field, f"%{value}"))
        )


def _discriminate_where_rule(
    v: Any,
) -> str:
    if isinstance(v, dict):
        if "rules" in v or "condition" in v:
            return "complex"
        return "simple"
    return "complex" if isinstance(v, _BaseComplexWhereRule) else "simple"


def _discriminate_operator(
    v: Any,
) -> str:
    if isinstance(v, dict):
        if "operator" in v and v["operator"] not in _Operators:
            return "unknown"
        return v["operator"]
    return v.operator


_SimpleWhereRule = Annotated[
    Union[
        Annotated[_BaseSimpleWhereRule, Tag("unknown")],
        Annotated[Equal, Tag(_Operators.EQUAL)],
        Annotated[IEqual, Tag(_Operators.IEQUAL)],
        Annotated[Like, Tag(_Operators.LIKE)],
        Annotated[ILike, Tag(_Operators.ILIKE)],
        Annotated[NotEqual, Tag(_Operators.NOTEQUAL)],
        Annotated[INotEquals, Tag(_Operators.INOTEQUAL)],
        Annotated[Contains, Tag(_Operators.CONTAINS)],
        Annotated[IContains, Tag(_Operators.ICONTAINS)],
        Annotated[In, Tag(_Operators.IN)],
        Annotated[NotIn, Tag(_Operators.NOTIN)],
        Annotated[GreaterThan, Tag(_Operators.GREATERTHAN)],
        Annotated[GreaterThanOrEqual, Tag(_Operators.GREATERTHANOREQUAL)],
        Annotated[LessThan, Tag(_Operators.LESSTHAN)],
        Annotated[LessThanOrEqual, Tag(_Operators.LESSTHANOREQUAL)],
        Annotated[IsNull, Tag(_Operators.ISNULL)],
        Annotated[IsNotNull, Tag(_Operators.ISNOTNULL)],
        Annotated[IsEmpty, Tag(_Operators.ISEMPTY)],
        Annotated[IsNotEmpty, Tag(_Operators.ISNOTEMPTY)],
        Annotated[StartsWith, Tag(_Operators.STARTSWITH)],
        Annotated[IStartsWith, Tag(_Operators.ISTARTSWITH)],
        Annotated[EndsWith, Tag(_Operators.ENDSWITH)],
        Annotated[IEndsWith, Tag(_Operators.IENDSWITH)],
    ],
    Discriminator(_discriminate_operator),
]


class _Conditions(str, Enum):
    AND = "and"
    OR = "or"
    NOT = "not"


class _BaseComplexWhereRule(_IRule):
    condition: _Conditions
    rules: list["WhereRule"] = PydanticField(..., min_length=1)

    @abstractmethod
    def join(self, compiled_rules: list):
        raise NotImplementedError()

    def compile(self, engine_context: EngineContext) -> Any:
        compiled_rules = [rule.compile(engine_context) for rule in self.rules]
        return self.join(compiled_rules)


class And(_BaseComplexWhereRule):
    condition: Literal[_Conditions.AND] = _Conditions.AND

    def join(self, compiled_rules: list):
        if len(compiled_rules) == 0:
            raise QueryBuilderSyntaxError(
                f"{_Conditions.AND} requires at least one rule"
            )
        return and_(*compiled_rules)


class Or(_BaseComplexWhereRule):
    condition: Literal[_Conditions.OR] = _Conditions.OR

    def join(self, compiled_rules: list):
        return or_(*compiled_rules)


class Not(_BaseComplexWhereRule):
    condition: Literal[_Conditions.NOT] = _Conditions.NOT
    rules: list["WhereRule"] = PydanticField(..., min_length=1, max_length=1)

    def join(self, compiled_rules: list):
        return not_(compiled_rules[0])


def _discriminate_condition(
    v: Any,
) -> str:
    if isinstance(v, dict):
        if "rules" in v or "condition" in v:
            if "condition" not in v or v["condition"] not in _Conditions:
                return "unknown"
            return v["condition"]
        return "unknown"
    return v.condition


ComplexWhereRule = Annotated[
    Union[
        Annotated[_BaseComplexWhereRule, Tag("unknown")],
        Annotated[And, Tag(_Conditions.AND)],
        Annotated[Or, Tag(_Conditions.OR)],
        Annotated[Not, Tag(_Conditions.NOT)],
    ],
    Discriminator(_discriminate_condition),
]


WhereRule = Annotated[
    Annotated[_SimpleWhereRule, Tag("simple")]
    | Annotated[ComplexWhereRule, Tag("complex")],
    Discriminator(_discriminate_where_rule),
]
