from app.api.schema.shared.base import CountMeta, BaseSchema
from app.api.schema.shared.entities import BaseEntitySchema
from app.core.models.main.user import User
from system.query_builder import Field


class UserSchema(BaseEntitySchema):
    name: str
    email: str
    phone: str
    address: str

    @staticmethod
    def get_query_builder_fields() -> list[Field]:
        return [
            Field("id", User.id),
            Field("email", User.email),
            Field("name", User.name),
        ]


class GetAllUsersResponse(BaseSchema):
    data: list[UserSchema]
    meta: CountMeta


class GetUserResponse(BaseSchema):
    data: UserSchema


class UpdateUserRequest(BaseSchema):
    name: str
    phone: str
    address: str


class CreateUserRequest(UpdateUserRequest):
    email: str
    password: str
