from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import ConfigDict


class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://root:ABCD%401234@localhost:3306/cairo_metro"
    SECRET_KEY: str = "aswa2daacswk21wd-122e23-daw231-321"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    paymob_api_key: str = (
        "ZXlKaGJHY2lPaUpJVXpVeE1pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SmpiR0Z6Y3lJNklrMWxjbU5vWVc1MElpd2ljSEp2Wm1sc1pWOXdheUk2TVRBME9UQTRPQ3dpYm1GdFpTSTZJbWx1YVhScFlXd2lmUS4wQURXQmxPZkZvMVAyU2pDd19kRjVLeUVfb1p2U0x4T0l6Wlk0TTdIbV9STkdMazRiU3MzYnQ5dUJ4cnFsRmJodlkyM2h5UElSTWN2eFVlYWFzaURZQQ"
    )
    paymob_hmac_secret: str = "8FA05AAC0BBFE7FDFAE6A1FEE4BBD08D"
    paymob_integration_id: str = "5110518"
    paymob_iframe_id: str = "927048"
    paymob_merchant_id: str = "1049088"

    model_config = ConfigDict(env_file=".env")


@lru_cache()
def get_settings():
    return Settings()
