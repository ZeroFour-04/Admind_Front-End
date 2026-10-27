from cliente_api.http import pedir


def listar(request):
    """GET /visitantes/ → visitantes del conjunto activo."""
    return pedir(request, "GET", "visitantes/")


def registrar(request, datos):
    """POST /visitantes/ → registra una entrada de visitante.

    `parqueadero` (id) es opcional y solo con vehículo. 400 bajo `parqueadero` si no es de visitantes;
    409 si otra visita lo ocupó antes: la visita no queda registrada.
    """
    return pedir(request, "POST", "visitantes/", datos)


def registrar_salida(request, visitante_id):
    """POST /visitantes/<id>/salida/ → la visita con `hora_salida`; su parqueadero queda libre. 409 si ya salió."""
    return pedir(request, "POST", f"visitantes/{visitante_id}/salida/")
