"""Endpoints de `Admind_Backend/apps/anuncios/`: el tablón del conjunto activo (HU-25)."""
from cliente_api.http import pedir, pedir_archivo


def listar(request):
    """GET /anuncios/ → los anuncios que la persona puede ver, el más reciente primero."""
    return pedir(request, "GET", "anuncios/")


def publicar(request, datos, fotos=()):
    """POST /anuncios/ → el anuncio publicado. Avisa una sola vez a sus destinatarios.

    Solo texto viaja en JSON. Con fotos viaja como formulario multipart, con el campo `fotos`
    repetido; ahí un dato en None (la vivienda de un anuncio al conjunto) no se manda.
    """
    archivos = [("fotos", (foto.name, foto.read(), foto.content_type)) for foto in fotos]
    return pedir(request, "POST", "anuncios/", datos, archivos=archivos)


def obtener(request, anuncio_id):
    """GET /anuncios/<id>/ → un anuncio visible para la persona, o 404."""
    return pedir(request, "GET", f"anuncios/{anuncio_id}/")


def editar(request, anuncio_id, datos):
    """PATCH /anuncios/<id>/ → el anuncio con el texto nuevo. No vuelve a avisar."""
    return pedir(request, "PATCH", f"anuncios/{anuncio_id}/", datos)


def foto(request, anuncio_id, foto_id):
    """GET /anuncios/<id>/fotos/<foto_id>/ → (contenido, tipo). 404 si la persona no ve ese anuncio."""
    return pedir_archivo(request, f"anuncios/{anuncio_id}/fotos/{foto_id}/")
