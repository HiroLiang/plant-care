import importlib


def test_main_module_imports_for_runtime_entrypoint():
    module = importlib.import_module("main")

    assert callable(module.main)
    assert callable(module.main_cli)


def test_cli_parser_defaults_match_bring_up_configuration():
    module = importlib.import_module("main")

    args = module.build_arg_parser().parse_args([])

    assert args.port == 50051
    assert args.channel == "can0"
    assert args.bitrate == 500000


def test_mcu_bus_daemon_module_wraps_cli_entrypoint():
    module = importlib.import_module("mcu_bus_daemon")

    assert module.main_cli is importlib.import_module("main").main_cli
