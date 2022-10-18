from pydantic import BaseSettings


class Settings(BaseSettings):
    base_dir: str
    log_dir: str

    billing_port: int
    inventory_port: int
    message_port: int
    order_port: int
    purchase_port: int

    class Config:
        env_file = ".env"
