import asyncio
from typing import Literal
import aiohttp

from .errors import CodeWaitTimeout, KopeechkaError


from .types import GeneralDict


class KopeechkaClient:
    def __init__(self, api_key: str, use_ssl: bool = False) -> None:
        self.api_key = api_key
        self._base_url = "https://api.kopeechka.store"
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=use_ssl)
        )

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()

    def append_common_params(self, path: str) -> str:
        return f"{path}&token={self.api_key}&type=JSON&api=2.0"

    async def _request(
        self,
        method: str,
        path: str,
    ) -> GeneralDict:
        url = self._base_url + self.append_common_params(path)

        async with self._session.request(method=method, url=url) as resp:
            await resp.read()

        return await resp.json()

    async def get_mail(
        self,
        site: str,
        mail_type: Literal[
            "ALL",
            "REAL",
            "MINE",
            "MAILCOM",
            "OUTLOOK",
            "MAILRU",
            "RAMBLER",
            "YANDEX",
            "GMX",
        ] = "MAILRU",
        mail_password: str = "rehmanali1337",
    ) -> GeneralDict:
        path = f"/mailbox-get-email?site={site}&mail_type={mail_type}&password={mail_password}"
        resp = await self._request("GET", path)

        if resp["status"] == "ERROR":
            return await self.get_mail(
                site=site, mail_type=mail_type, mail_password=mail_password
            )
        return resp

    async def get_verification_code(
        self,
        mail_id: str,
        full: Literal["0", "1"] = "0",
        check_every: int = 3,
        max_wait_seconds: int = 180,
    ) -> str:
        current_wait: int = 0
        while current_wait < max_wait_seconds:
            path = f"/mailbox-get-message?id={mail_id}&full={full}"
            resp = await self._request("GET", path)
            if resp["status"] == "ERROR" and resp["value"] == "WAIT_LINK":
                # print(
                #     f"Waiting for {check_every} seconds before checking for email message again ... Current wait: {current_wait}"
                # )
                await asyncio.sleep(check_every)
                current_wait += check_every
                continue

            elif resp["status"] == "OK":
                return resp["value"]

            else:
                raise KopeechkaError(resp.__str__())

        raise CodeWaitTimeout(
            f"Could not receive the verification code in {max_wait_seconds} seconds."
        )
