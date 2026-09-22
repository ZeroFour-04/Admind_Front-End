"""Endpoints de `Admind_Backend/apps/anuncios/`: el tablón del conjunto activo (HU-25)."""
from cliente_api.http import pedir


def listar(request):
    """GET /anuncios/ → los anuncios que la persona puede ver, el más reciente primero."""
    return pedir(request, "GET", "anuncios/")


def publicar(request, datos):
    """POST /anuncios/ → el anuncio publicado. Avisa una sola vez a sus destinatarios."""
    return pedir(request, "POST", "anuncios/", datos)


def obtener(request, anuncio_id):
    """GET /anuncios/<id>/ → un anuncio visible para la persona, o 404."""
    return pedir(request, "GET", f"anuncios/{anuncio_id}/")


def editar(request, anuncio_id, datos):
    """PATCH /anuncios/<id>/ → el anuncio con el texto nuevo. No vuelve a avisar."""
    return pedir(request, "PATCH", f"anuncios/{anuncio_id}/", datos)
