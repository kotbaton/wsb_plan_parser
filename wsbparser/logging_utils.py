import logging


LOG_FORMAT = "%(levelname)s: %(message)s"


def resolve_log_level(verbose: int) -> int:
    if verbose >= 2:
        return logging.DEBUG
    if verbose >= 1:
        return logging.INFO
    return logging.WARNING


def configure_logging(verbose: int = 0) -> None:
    logging.basicConfig(
        level=resolve_log_level(verbose),
        format=LOG_FORMAT,
        force=True,
    )

