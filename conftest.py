import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--config", action="store", default='secrets/test-config.json', help="Connection configuration file"
    )

@pytest.fixture(scope='session')
def config_file(request):
    return request.config.getoption("--config")

