from fastapi import APIRouter

from .helpers import wrap_to_http_exc
from ..rutracker_api import RutrackerApi


router = APIRouter(prefix='/v1', tags=['Rutracker endpoints'])
router.add_api_route('/search', wrap_to_http_exc(RutrackerApi.search), methods=['GET'])
router.add_api_route('/search/{search_id:str}/{page:int}', wrap_to_http_exc(RutrackerApi.pagination), methods=['GET'])
router.add_api_route('/download/{content_id:str}', wrap_to_http_exc(RutrackerApi.download_torrent), methods=['GET'])
router.add_api_route('/view/{content_id:str}', wrap_to_http_exc(RutrackerApi.content_view), methods=['GET'])
