"""Endpoints de `Admind_Backend/apps/conjuntos/`: el asistente de creación (HU-03) y la identidad visual (HU-21)."""
from cliente_api.http import pedir, pedir_archivo


def crear(request, datos):
    """POST /conjuntos/ → {conjunto, ...estado de la sesión}. El conjunto nuevo queda como activo."""
    return pedir(request, "POST", "conjuntos/", datos)


def resumen(request):
    """GET /conjuntos/actual/ → {conjunto, administradores, requisitos, puede_activar} del conjunto activo."""
    return pedir(request, "GET", "conjuntos/actual/")


def editar(request, datos):
    """PATCH /conjuntos/actual/ → el resumen actualizado."""
    return pedir(request, "PATCH", "conjuntos/actual/", datos)


def activar(request):
    """POST /conjuntos/actual/activar/ → el resumen, o 400 con los requisitos que faltan."""
    return pedir(request, "POST", "conjuntos/actual/activar/")


# Identidad visual (HU-21)


def identidad(request):
    """GET /conjuntos/actual/identidad/ → {id, nombre, acento, logo} del conjunto activo."""
    return pedir(request, "GET", "conjuntos/actual/identidad/")


def cambiar_acento(request, acento, color=None):
    """PATCH /conjuntos/actual/identidad/ → la identidad con el color nuevo.

    `color` solo va con el acento personalizado: es el hex elegido en el selector del navegador.
    """
    datos = {"acento": acento, **({"color": color} if color else {})}
    return pedir(request, "PATCH", "conjuntos/actual/identidad/", datos)


def subir_logo(request, archivo):
    """PUT /conjuntos/actual/identidad/logo/ → la identidad con la huella del logo nuevo, o 400."""
    contenido = (archivo.name, archivo.read(), archivo.content_type)
    return pedir(request, "PUT", "conjuntos/actual/identidad/logo/", archivos={"archivo": contenido})


def quitar_logo(request):
    """DELETE /conjuntos/actual/identidad/logo/ → la identidad sin logo."""
    return pedir(request, "DELETE", "conjuntos/actual/identidad/logo/")


def imagen_del_logo(request, huella):
    """GET /conjuntos/logos/<huella>/ → (contenido, tipo). 404 si no es de un conjunto disponible."""
    return pedir_archivo(request, f"conjuntos/logos/{huella}/")
