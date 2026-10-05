"""Pantallas de HU-01 para recuperar la contraseña: pedir el enlace y crear la nueva. La API se simula."""
from unittest import mock

from django.test import Client

from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi
from tests.ayudantes import cliente_con_sesion

ENVIADO = {"detail": "Si el correo está registrado, te enviamos un enlace para restablecer la contraseña."}
DEMASIADOS = "Se pidieron demasiados enlaces para este correo. Espera una hora e intenta de nuevo."
ENLACE = "/restablecer-contrasena/MTIz/abc-123/"
CLAVE = "otra-clave-larga-2026"


def test_pedir_el_enlace_no_exige_sesion():
    respuesta = Client().get("/recuperar-contrasena/")

    assert respuesta.status_code == 200
    assert "Enviar enlace" in respuesta.content.decode()


def test_pedir_el_enlace_manda_el_correo_a_la_api_y_muestra_su_respuesta():
    with mock.patch("cliente_api.cuentas.solicitar_recuperacion", return_value=ENVIADO) as api:
        html = Client().post("/recuperar-contrasena/", {"correo": "laura@correo.com"}).content.decode()

    assert api.call_args.args[1] == "laura@correo.com"
    assert 'role="status">Si el correo está registrado' in html
    assert "Enviar enlace" not in html


def test_un_correo_mal_escrito_no_llega_a_la_api():
    with mock.patch("cliente_api.cuentas.solicitar_recuperacion") as api:
        html = Client().post("/recuperar-contrasena/", {"correo": "no-es-un-correo"}).content.decode()

    api.assert_not_called()
    assert "am-campo__error" in html


def test_pasado_el_limite_se_muestra_el_mensaje_de_la_api():
    limite = ErrorDeApi(429, {"detail": DEMASIADOS})
    with mock.patch("cliente_api.cuentas.solicitar_recuperacion", side_effect=limite):
        html = Client().post("/recuperar-contrasena/", {"correo": "laura@correo.com"}).content.decode()

    assert 'role="alert"' in html
    assert DEMASIADOS in html


def test_con_la_api_apagada_la_pantalla_lo_dice():
    with mock.patch("cliente_api.cuentas.solicitar_recuperacion", side_effect=ApiNoDisponible()):
        html = Client().post("/recuperar-contrasena/", {"correo": "laura@correo.com"}).content.decode()

    assert 'role="alert"' in html
    assert MENSAJE_API_NO_DISPONIBLE in html


def test_la_contrasena_nueva_viaja_a_la_api_con_el_uid_y_el_token_del_enlace():
    cliente = cliente_con_sesion()
    with mock.patch("cliente_api.cuentas.restablecer_contrasena") as api:
        respuesta = cliente.post(ENLACE, {"contrasena": CLAVE, "confirmacion": CLAVE})

    assert api.call_args.args[1:] == ("MTIz", "abc-123", CLAVE)
    assert respuesta["Location"] == "/?restablecida=1"
    # La API cerró todas las sesiones de la cuenta: la de este navegador también se cierra.
    assert "token_api" not in cliente.session


def test_si_las_dos_contrasenas_no_coinciden_no_se_llama_a_la_api():
    with mock.patch("cliente_api.cuentas.restablecer_contrasena") as api:
        html = Client().post(ENLACE, {"contrasena": CLAVE, "confirmacion": CLAVE + "x"}).content.decode()

    api.assert_not_called()
    assert "Las dos contraseñas no coinciden." in html


def test_un_enlace_vencido_se_avisa_arriba_del_formulario():
    vencido = ErrorDeApi(400, {"detail": "El enlace no es válido o ya venció. Pide uno nuevo."})
    with mock.patch("cliente_api.cuentas.restablecer_contrasena", side_effect=vencido):
        html = Client().post(ENLACE, {"contrasena": CLAVE, "confirmacion": CLAVE}).content.decode()

    assert 'role="alert"' in html
    assert "El enlace no es válido o ya venció. Pide uno nuevo." in html
    assert "Pedir otro enlace" in html


def test_una_contrasena_debil_se_explica_bajo_su_campo():
    debil = ErrorDeApi(400, {"contrasena": ["Esta contraseña es demasiado corta."]})
    with mock.patch("cliente_api.cuentas.restablecer_contrasena", side_effect=debil):
        html = Client().post(ENLACE, {"contrasena": "123", "confirmacion": "123"}).content.decode()

    assert 'id="id_contrasena-error">Esta contraseña es demasiado corta.' in html
    assert 'role="alert"' not in html


def test_despues_de_cambiarla_el_ingreso_lo_confirma():
    aviso = "Tu contraseña cambió. Inicia sesión con la nueva."

    assert aviso in Client().get("/?restablecida=1").content.decode()
    assert aviso not in Client().get("/").content.decode()
