import reflex as rx

from nanapi.fastapi import app as fastapi_app

app = rx.App(api_transformer=fastapi_app)
