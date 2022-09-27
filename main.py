import os
import sys

import aiohttp
import asyncio
import re

from bs4 import BeautifulSoup
from telebot.async_telebot import AsyncTeleBot
from collections import deque


class Parser:
    def __init__(self, url):
        self.url = url

    async def load_html(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                print("Status:", response.status)
                print("Content-type:", response.headers["content-type"])
                if response.ok:
                    return await response.text()
                return ""

    async def parse_ip(self):
        pass

    async def parse_location(self):
        pass

    async def get_info(self):
        ip = await self.parse_ip()
        location = await self.parse_location()
        return f"ip: {ip}\nlocation: {location}"


class SoupParser(Parser):
    _soup = None

    async def get_soup(self):
        if not self._soup:
            html = await self.load_html()
            self._soup = BeautifulSoup(html, features="html.parser")
        return self._soup

    async def clean(self):
        self._soup = None

    async def get_info(self):
        result = await super(SoupParser, self).get_info()
        await self.clean()
        return result


class YandexParser(SoupParser):
    async def parse_ip(self):
        soup = await self.get_soup()
        return (
            soup.find("section", {"class": "layout__top-section"})
            .find("div", text=re.compile("(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3})"))
            .text.strip()
        )

    async def parse_location(self):
        soup = await self.get_soup()
        return (
            soup.find("section", {"class": "layout__top-section"})
            .find("div", {"class": "location-renderer__value"})
            .text.strip()
        )


class Ip2Parser(SoupParser):
    async def parse_ip(self):
        soup = await self.get_soup()
        return soup.find("div", {"class": "ip-info"}).find("span").text.strip()

    async def parse_location(self):
        soup = await self.get_soup()
        return soup.find("div", {"class": "value-country"}).text.strip()


token = os.getenv("TOKEN")
bot = AsyncTeleBot(token)
bot.parsers = deque()
bot.parsers.extend(
    [
        Ip2Parser("https://2ip.ru/"),
        YandexParser("https://yandex.ru/internet"),
    ]
)


async def get_info():
    max_attemps = 10
    attempts = max_attemps
    info = None
    while info is None and attempts:
        attempts -= 1
        parser = bot.parsers.pop()
        print(f"attemps: {max_attemps-attempts}  parser: {parser.url}")
        bot.parsers.appendleft(parser)
        try:
            info = await parser.get_info()
        except Exception as ex:
            print(ex, file=sys.stderr)
    return info


@bot.message_handler(commands=["ip"])
async def send_ip_info(message):
    print(f"request from user: {message.from_user}")

    await bot.reply_to(
        message,
        await get_info(),
    )


asyncio.run(bot.infinity_polling())
