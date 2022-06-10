import asyncio
import json
from aiohttp import ClientSession

async def test():
    async with ClientSession() as session:
        async with session.get(f"https://hcaptcha.com/siteverify?response={hcap_token}&secret={secret_key_hca}") as resp:
            respnse = json.loads(await resp.text())
            await session.close()

    return respnse


def check():
    ar = asyncio.run(test())

    return ar


print(check())
#https://hcaptcha.com/siteverify?response={hcap_token}&secret={secret_key_hca}