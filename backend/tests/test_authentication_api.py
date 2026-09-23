from fastapi.testclient import TestClient


def test_authentication_flow_registers_logs_in_reads_user_and_logs_out(
    api_client: TestClient,
) -> None:
    registration = api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "flow@example.com",
            "password": "synthetic passphrase 2026",
        },
    )
    login = api_client.post(
        "/api/v1/auth/login",
        json={
            "email": "FLOW@example.com",
            "password": "synthetic passphrase 2026",
        },
    )

    assert registration.status_code == 201
    assert login.status_code == 200
    token_body = login.json()
    assert token_body["token_type"] == "bearer"
    assert "access_token" in token_body
    assert "expires_at" in token_body

    authorization = {"Authorization": f"Bearer {token_body['access_token']}"}
    current_user = api_client.get("/api/v1/auth/me", headers=authorization)
    logout = api_client.post("/api/v1/auth/logout", headers=authorization)
    after_logout = api_client.get("/api/v1/auth/me", headers=authorization)

    assert current_user.status_code == 200
    assert current_user.json()["email"] == "flow@example.com"
    assert logout.status_code == 204
    assert logout.content == b""
    assert after_logout.status_code == 401
    assert after_logout.headers["www-authenticate"] == "Bearer"


def test_login_returns_same_error_for_unknown_user_and_wrong_password(
    api_client: TestClient,
) -> None:
    api_client.post(
        "/api/v1/auth/register",
        json={
            "email": "known@example.com",
            "password": "synthetic passphrase 2026",
        },
    )

    unknown_user = api_client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "synthetic passphrase 2026",
        },
    )
    wrong_password = api_client.post(
        "/api/v1/auth/login",
        json={
            "email": "known@example.com",
            "password": "incorrect synthetic passphrase",
        },
    )

    assert unknown_user.status_code == 401
    assert wrong_password.status_code == 401
    assert (
        unknown_user.json()
        == wrong_password.json()
        == {"detail": "Invalid email or password"}
    )


def test_me_requires_bearer_token(api_client: TestClient) -> None:
    response = api_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
