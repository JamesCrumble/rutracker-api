import re
import httpx

from pathlib import Path
from bs4.element import Tag
from http import HTTPStatus
from base64 import b64encode
from bs4 import BeautifulSoup
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from .schemas import RutrackerTableRow, SearchResult, ContentView
from .exceptions import RutrackerRequestError, RutrackerApiError, RutrackerSearchSessionExpired
from ..settings import settings

TOTAL_RESULT_PATTERN: re.Pattern = re.compile(r'Результатов поиска: (\d{,3})')
SEARCH_ID_PATTERN: re.Pattern = re.compile(r'PG_BASE_URL: \'tracker\.php\?search_id=(.+)\'')
ROWS_PER_PAGE_PATTERN: re.Pattern = re.compile(r'PG_PER_PAGE: \'?(\d{,3})\'?')


def content_view_exclude_useless_text_tags(content_view_body: BeautifulSoup) -> None:
    if clear_tag := content_view_body.find(class_='clear'):
        clear_tag.extract()
    if info_footer := content_view_body.find_all(class_='post-align'):
        info_footer[-1].extract()

    for wrap_ in content_view_body.find_all(class_='sp-wrap'):
        wrap_.extract()


def parse_search_result(parser: BeautifulSoup) -> list[RutrackerTableRow]:
    skip: int = 0
    table = parser.find(id='tor-tbl')

    header: list[str] = list()
    result: list[RutrackerTableRow] = list()

    for i, tag in enumerate(table.find('thead').find_all('th')):
        tag: Tag

        column = tag.attrs.get('title', tag.text)
        if column == '\xa0':
            skip = i + 1
            continue

        header.append(column)

    for tag in table.find('tbody').find_all('tr'):
        tag: Tag
        row: list[Tag] = tag.find_all('td')[skip:]
        if not row:
            continue

        row = RutrackerTableRow.from_raw(row)
        result.append(row)

    return result


def parse_search_page(response_content: str) -> SearchResult:
    parser = BeautifulSoup(response_content, 'html.parser')

    result = SearchResult.empty()
    result.rows = parse_search_result(parser)
    if not result.rows:
        return result

    total_result_match = TOTAL_RESULT_PATTERN.search(response_content)
    assert total_result_match is not None, 'Cannot define total search results'

    search_id_match = SEARCH_ID_PATTERN.search(response_content)
    if search_id_match is not None:
        result.search_id = search_id_match.group(1)

    total_result = int(total_result_match.group(1))
    div, mod = divmod(total_result, len(result.rows))

    result.total_pages = div if mod == 0 else div + 1
    result.total_founded_rows = total_result

    return result


class RutrackerApi:

    __rows_per_page__: int = 50  # 50 by default and updates with each search request

    __login_endpoint__: str = settings.RUTRACKER_BASE_URL + '/login.php'
    __search_endpoint__: str = settings.RUTRACKER_BASE_URL + '/tracker.php'
    __download_endpoint__: str = settings.RUTRACKER_BASE_URL + '/dl.php'
    __content_view_endpoint__: str = settings.RUTRACKER_BASE_URL + '/viewtopic.php'

    @classmethod
    def _update_rows_per_page(cls, response_content: str) -> None:
        rows_per_page_match = ROWS_PER_PAGE_PATTERN.search(response_content)
        if rows_per_page_match is None:  # This is fine couse option doesn't shown on little results
            return

        cls.__rows_per_page__ = int(rows_per_page_match.group(1))

    @classmethod
    def _validate_response(cls, response: httpx.Response) -> None:
        if response.status_code != HTTPStatus.OK:
            raise RutrackerRequestError(response)
        if response.text.startswith('Ошибочный запрос:'):
            raise RutrackerRequestError(response, response.text)
        if 'Сессия устарела' in response.text:
            raise RutrackerSearchSessionExpired()

    @classmethod
    @asynccontextmanager
    async def _async_proxy_client(cls) -> AsyncGenerator[httpx.AsyncClient]:
        cookies = {"bb_session": settings.RUTRACKER_SESSION_COOKIE}
        async with httpx.AsyncClient(proxy=settings.PROXY_DSN, cookies=cookies) as client:
            yield client

    @classmethod
    async def content_view(cls, content_id: str) -> ContentView:
        async with cls._async_proxy_client() as client:
            response = await client.get(cls.__content_view_endpoint__, params={'t': content_id})
            cls._validate_response(response)

            parser = BeautifulSoup(response.content, 'html.parser')
            content_view_body = parser.find(class_='post_body')

            content_view_body_text: str = ''
            content_view_title: str | None = None
            content_view_image_bs64: str | None = None
            content_view_image_link: str | None = None

            possibly_content_view_title = content_view_body.next.next
            if type(possibly_content_view_title) is Tag:
                if 'post-align' in possibly_content_view_title.attrs.get('class', []):
                    possibly_content_view_title = possibly_content_view_title.next

                if possibly_content_view_title.attrs.get('style', '').startswith('font-size'):
                    content_view_title = possibly_content_view_title.extract().text

            content_view_image_link_tag = content_view_body.find(class_='postImg').extract()
            content_view_image_link = content_view_image_link_tag.attrs.get('src', content_view_image_link_tag.attrs.get('title'))

            content_view_exclude_useless_text_tags(content_view_body)
            content_view_body_text = content_view_body.text.strip()

            if content_view_image_link is not None:
                content_view_image_response = await client.get(content_view_image_link)
                if content_view_image_response.status_code == HTTPStatus.OK:
                    content_view_image_bs64 = b64encode(content_view_image_response.content)

            return ContentView(
                title=content_view_title,
                body=content_view_body_text,
                image_bs64=content_view_image_bs64,
            )

    @classmethod
    async def download_torrent(cls, content_id: str) -> None:
        fp = Path(settings.DOWNLOAD_FOLDER_PATH) / f'{content_id}.torrent'
        added_to_downloading_fp = Path(settings.DOWNLOAD_FOLDER_PATH) / f'{content_id}.torrent.added'
        if fp.exists() or added_to_downloading_fp.exists():
            return

        handle = open(fp, 'wb')
        try:
            async with cls._async_proxy_client() as client:
                async with client.stream('POST', cls.__download_endpoint__, params={'t': content_id}) as response:
                    async for chunk in response.aiter_bytes(settings.DOWNLOADING_CHUNK_SIZE):
                        handle.write(chunk)
        except Exception as exc:
            fp.unlink()
            raise RutrackerApiError(exc)
        finally:
            handle.close()

    @classmethod
    async def pagination(cls, search_id: str, page: int) -> SearchResult:
        if page <= 0:
            raise RutrackerRequestError('Page number should be greater than 0.')

        async with cls._async_proxy_client() as client:
            response = await client.get(
                cls.__search_endpoint__, params={'search_id': search_id, 'start': (page - 1) * cls.__rows_per_page__}
            )
            cls._validate_response(response)

            response_content = response.text
            cls._update_rows_per_page(response_content)

            result = parse_search_page(response_content)
            if result.rows:
                result.page = page

            return result

    @classmethod
    async def search(cls, query: str) -> SearchResult:
        async with cls._async_proxy_client() as client:
            response = await client.post(cls.__search_endpoint__, params={'nm': query})
            cls._validate_response(response)

            response_content = response.text
            cls._update_rows_per_page(response_content)

            result = parse_search_page(response_content)
            if result.rows:
                result.page = 1

            return result


# python -m src.rutracker_api.api
if __name__ == '__main__':
    import random  # noqa
    import asyncio  # noqa

    async def main() -> None:
        search_query = 'Чужой: Ромул'
        print('#'*40, f' SEARCH "{search_query}" ', '#'*40, '\n\n')
        result = await RutrackerApi.search(search_query)
        print(f'Result: {result.page=} {result.total_pages=} {result.search_id=}')
        for row in result.rows:
            print(f'{row.label=}, {row.size=}, {row.content_id=}')
        print('\n\n')

        random_row: RutrackerTableRow = random.choice([row for row in result.rows if row.content_id is not None])

        print('#'*40, f' DOWNLOADING "{random_row.content_id}" ', '#'*40, '\n')
        await RutrackerApi.download_torrent(random_row.content_id)

    asyncio.run(main())
