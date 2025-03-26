from uuid6 import uuid7


def generate_uuid(prefix: str | None = None) -> str:
    uuid_parts = []

    if prefix:
        uuid_parts.append(prefix)

    formatted_uuid = str(uuid7()).replace("-", "")
    uuid_parts.append(formatted_uuid)

    return "_".join(uuid_parts)
