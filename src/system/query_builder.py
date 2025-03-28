from abc import ABC, abstractmethod
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

SimpleWhere = Annotated[Union["Equal", "NotEqual"], Field(discriminator="operator")]
ComplexWhere = Annotated[Union["And", "Or"], Field(discriminator="condition")]
Where = Union[SimpleWhere, ComplexWhere]


class IRule(BaseModel, ABC):
    """
    Interface for a rule in the query builder.
    """

    @abstractmethod
    def compile(self):
        raise NotImplementedError("QueryBuilder rules must implement this method.")


# SimpleWhere
class ISimpleWhere(IRule):
    field: str


class Equal(ISimpleWhere):
    operator: Literal["equal"] = "equal"
    value: str

    def compile(self):
        return f"{self.field} = '{self.value}'"


class NotEqual(ISimpleWhere):
    operator: Literal["not_equal"] = "not_equal"
    value: str

    def compile(self):
        return f"{self.field} != '{self.value}'"


# ComplexWhere
class IComplexWhere(IRule):
    rules: list["Where"]


class And(IComplexWhere):
    condition: Literal["and"] = "and"

    def compile(self):
        return " AND ".join(rule.compile() for rule in self.rules)


class Or(IComplexWhere):
    condition: Literal["or"] = "or"

    def compile(self):
        return " OR ".join(rule.compile() for rule in self.rules)


class Filters(BaseModel):
    filters: Where


if __name__ == "__main__":
    # Example usage
    # raw_query = {"filters": {"field": "age", "operator": "not_equal", "value": "30"}}
    raw_query = {
        "filters": {
            "condition": "or",
            "rules": [
                {"field": "age", "operator": "not_equal", "value": "30"},
                {"field": "name", "operator": "equal", "value": "John"},
            ],
        }
    }

    filters_instance = Filters.model_validate(raw_query)
    print(filters_instance.filters.compile())
