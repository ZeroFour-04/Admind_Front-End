from cliente_api.http import pedir


def listar(request):
    """GET /visitantes/ → visitantes del conjunto activo."""
    return pedir(request, "GET", "visitantes/")


def registrar(request, datos):
    """POST /visitantes/ → registra una entrada de visitante."""
    return pedir(request, "POST", "visitantes/", datos)
