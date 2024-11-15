from bs4.element import Tag
from pydantic import BaseModel


class RutrackerTableRow(BaseModel):
    forum: str
    label: str
    author: str
    size: str
    size_bytes: int
    sids: int
    leeches: int
    downloaded_times: int
    created: str
    content_id: str | None = None

    @staticmethod
    def from_raw(row: list[Tag]) -> 'RutrackerTableRow':
        forum, label, author, size, sids, leeches, downloaded_times, created = row

        content_id = None
        if label.find('a') is not None:
            content_id = str(label.find('a').attrs['data-topic_id'])

        sids_raw = str(sids.text.strip())

        return RutrackerTableRow(
            forum=forum.text.strip(),
            label=label.text.strip(),
            author=author.text.strip(),
            size=' '.join(size.text.strip().replace('\xa0', ' ').split(' ')[:2]),
            size_bytes=int(size.attrs['data-ts_text']),
            sids=int(sids_raw) if sids_raw.isdigit() else 0,
            leeches=int(leeches.text.strip()),
            downloaded_times=int(downloaded_times.text.strip()),
            created=created.text.strip(),
            content_id=content_id,
        )


class SearchResult(BaseModel):
    rows: list[RutrackerTableRow]
    page: int
    total_pages: int
    total_founded_rows: int
    search_id: str | None

    @staticmethod
    def empty() -> 'SearchResult':
        return SearchResult(
            rows=list(),
            page=0,
            total_pages=0,
            total_founded_rows=0,
            search_id=None,
        )
