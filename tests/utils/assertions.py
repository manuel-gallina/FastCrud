from httpx import Response


def assert_api_error_format(response: Response) -> None:
    response_content = response.json()
    assert (
        "error" in response_content
    ), "Error response does not contain an error object"
    assert (
        "requestId" in response_content["error"]
    ), "Error response does not contain a requestId"
    assert "code" in response_content["error"], "Error response does not contain a code"
    assert (
        "message" in response_content["error"]
    ), "Error response does not contain a message"
    assert (
        "detail" in response_content["error"]
    ), "Error response does not contain a detail"
