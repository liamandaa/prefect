import typing as t
import uuid

import pydantic
import pytest
from prefect._vendor.fastapi.testclient import TestClient

from prefect import flow
from prefect.runner import Runner
from prefect.runner.server import build_server


@pytest.fixture(scope="function")
def tmp_runner_env(monkeypatch):
    monkeypatch.setenv("PREFECT_RUNNER_SERVER_HOST", "0.0.0.0")
    monkeypatch.setenv("PREFECT_RUNNER_SERVER_PORT", "0")


@pytest.fixture(scope="function")
async def runner(tmp_runner_env) -> Runner:
    return Runner()


async def create_deployment(runner: Runner, func: t.Callable):
    # Use unique names to force multiple deployments to be created
    deployment_id = await runner.add_flow(
        func, f"{uuid.uuid4()}", enforce_parameter_schema=True
    )
    return str(deployment_id)


async def test_runners_deployment_run_routes_exist(runner: Runner):
    @flow(version="test")
    def f(verb: str = "party"):
        print(f"I'm just here to {verb}")

    deployment_ids = [await create_deployment(runner, f) for _ in range(3)]
    webserver = await build_server(runner)

    deployment_run_routes = [
        r
        for r in webserver.routes
        if r.path.startswith("/deployment") and r.path.endswith("/run")
    ]
    deployment_run_paths = {r.path for r in deployment_run_routes}

    # verify that all deployment routes correspond to one of the deployments
    for route in deployment_run_routes:
        id_ = route.path.split("/")[2]
        assert id_ in deployment_ids

    # verify that all deployments have a route
    for id_ in deployment_ids:
        route = f"/deployment/{id_}/run"
        assert route in deployment_run_paths


async def test_runners_deployment_run_route_does_input_validation(runner: Runner):
    @flow(version="test")
    def f(verb: str = "party"):
        print(f"I'm just here to {verb}")

    deployment_id = await create_deployment(runner, f)
    webserver = await build_server(runner)

    client = TestClient(webserver)
    response = client.post(f"/deployment/{deployment_id}/run", json={"verb": False})
    assert response.status_code == 400

    response = client.post(f"/deployment/{deployment_id}/run", json={"verb": "clobber"})
    assert response.status_code == 201


async def test_runners_deployment_run_route_with_complex_args(runner: Runner):
    class A(pydantic.BaseModel):
        a: int = 0

    class B(pydantic.BaseModel):
        a: A = A()
        b: bool = False

    @flow
    def complex_flow(
        x: int, y: str = "hello", z: t.List[bool] = [True], a: A = A(), b: B = B()
    ):
        print(x, y, z, a, b)

    deployment_id = await runner.add_flow(
        complex_flow, f"{uuid.uuid4()}", enforce_parameter_schema=True
    )
    webserver = await build_server(runner)
    client = TestClient(webserver)
    response = client.post(f"/deployment/{deployment_id}/run", json={"x": 100})
    assert response.status_code == 201, response.json()
