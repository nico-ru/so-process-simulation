from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    general settings for system behavior
    """

    availability_rate: float = 0.8

    """
    anomaly induction rates and codes
    sequence anomalies
    """
    swap_event_rate: float = 0.004  # swap
    skip_event_rate: float = 0.004  # skip
    repeat_event_rate: float = 0.004  # repeat

    swap_event_code: int = 8
    skip_event_code: int = 16
    repeat_event_code: int = 32

    """
    point anomalies
    """
    add_key_rate: float = 0.004  # new
    skip_key_rate: float = 0.004  # missing
    modify_key_rate: float = 0.004  # change

    add_key_code: int = 4
    skip_key_code: int = 2
    modify_key_code: int = 1

    class Config:
        env_file = ".env"
