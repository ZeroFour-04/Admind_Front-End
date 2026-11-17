"""Las páginas de error propias y la traducción de los errores de la API que nadie atrapó."""
from django.test import Client, RequestFactory
from django.contrib.sessions.backends.db import SessionStore

from apps.cuentas.errores import ErroresDeApiMiddleware
from cliente_api.http import ApiNoDisponible, ErrorDeApi, NoAutenticado
from tests.ayudantes import cliente_con_sesion


def traducir(excepcion):
    peticion = RequestFactory().get("/anuncios/")
    peticion.session = SessionStore()
    peticion.session["token_api"] = "token-de-prueba"
    respuesta = ErroresDeApiMiddleware(lambda r: None).process_exception(peticion, excepcion)
    return respuesta, peticion


def test_una_ruta_que_no_existe_muestra_la_pagina_propia_y_no_la_de_django():
    respuesta = cliente_con_sesion().get("/esto-no-existe/")
    html = respuesta.content.decode()

    assert respuesta.status_code == 404
    assert "No encontramos esa página" in html and "Volver al inicio" in html
    assert "Page not found" not in html


def test_un_formulario_vencido_muestra_la_pagina_de_la_pagina_vencida():
    respuesta = Client(enforce_csrf_checks=True).post("/", {"correo": "a@b.co", "contrasena": "x"})
    html = respuesta.content.decode()

    assert respuesta.status_code == 403
    assert "La página venció" in html and "CSRF" not in html


def test_si_la_api_no_responde_se_avisa_que_el_servidor_no_responde():
    respuesta, _ = traducir(ApiNoDisponible())

    assert respuesta.status_code == 503
    assert "El servidor no responde" in respuesta.content.decode()


def test_un_403_de_la_api_sin_atrapar_dice_que_no_tiene_acceso():
    respuesta, _ = traducir(ErrorDeApi(403, {"detail": "no"}))
    html = respuesta.content.decode()

    assert respuesta.status_code == 403
    assert "No tienes acceso a esta página" in html and "No tienes permiso para hacer esto" in html


def test_un_404_de_la_api_sin_atrapar_dice_que_no_existe_sin_confirmar_nada_mas():
    respuesta, _ = traducir(ErrorDeApi(404, None))

    assert respuesta.status_code == 404
    assert "No encontramos esa página" in respuesta.content.decode()


def test_un_error_del_servidor_de_la_api_no_muestra_el_cuerpo_crudo():
    respuesta, _ = traducir(ErrorDeApi(500, {"detail": "Traceback (most recent call last)"}))
    html = respuesta.content.decode()

    assert respuesta.status_code == 500
    assert "Traceback" not in html and "no pudo atender la petición" in html


def test_con_la_sesion_vencida_en_la_api_se_cierra_la_sesion_y_se_vuelve_al_ingreso():
    respuesta, peticion = traducir(NoAutenticado(401, None))

    assert respuesta.status_code == 302 and respuesta.url == "/"
    assert "token_api" not in peticion.session


def test_otros_errores_de_python_siguen_su_camino():
    respuesta, _ = traducir(ValueError("algo"))

    assert respuesta is None


def test_la_pagina_500_se_arma_sin_sesion_ni_contexto():
    from django.views.defaults import server_error

    respuesta = server_error(RequestFactory().get("/"))

    assert respuesta.status_code == 500
    assert "Algo salió mal de nuestro lado" in respuesta.content.decode()
