def pytest_addoption(parser):
    parser.addoption("--mode", action="store")
    parser.addoption("--tty", action="store")
