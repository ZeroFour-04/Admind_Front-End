"""Pantallas de HU-02 para quien perdió la aplicación de autenticación: pedir el enlace y confirmarlo. La API se simula."""
from unittest import mock

from django.test import Client

from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi
from tests.ayudantes import cliente_con_sesion

ENVIADO = {"detail": "Te enviamos al correo de tu cuenta un enlace para quitar la verificación en dos pasos."}
DEMASIADOS = "Se pidieron demasiados enlaces para esta cuenta. Espera una hora e intenta de nuevo."
VENCIDO = "El enlace no es válido o ya venció. Pide uno nuevo."
ENLACE = "/segundo-factor/restablecer/MTIz/abc-123/"


def cliente_sin_verificar():
    """Entró con su contraseña y le falta el segundo paso."""
    cliente = cliente_con_sesion()
    sesion = cliente.session
    sesion["dos_factores"] = {"requerido": True, "configurado": True, "verificado": False}
    sesion.save()
    return cliente


def test_la_verificacion_enlaza_la_ayuda_para_quien_perdio_la_aplicacion():
    html = cliente_sin_verificar().get("/segundo-factor/verificar/").content.decode()

    assert '<a href="/segundo-factor/problemas/">¿Problemas con la verificación en dos pasos?</a>' in html


def test_la_ayuda_se_abre_con_el_segundo_factor_pendiente():
    respuesta = cliente_sin_verificar().get("/segundo-factor/problemas/")

    assert respuesta.status_code == 200
    assert "Enviar enlace a mi correo" in respuesta.content.decode()


def test_sin_sesion_la_ayuda_manda_al_ingreso():
    respuesta = Client().get("/segundo-factor/problemas/")

    assert respuesta.status_code == 302
    assert respuesta["Location"] == "/"


def test_pedir_el_enlace_llama_a_la_api_y_muestra_su_respuesta():
    with mock.patch("cliente_api.cuentas.solicitar_restablecer_dos_factores", return_value=ENVIADO) as api:
        html = cliente_sin_verificar().post("/segundo-factor/problemas/").content.decode()

    api.assert_called_once()
    assert 'role="status">Te enviamos al correo de tu cuenta' in html
    assert "Enviar enlace a mi correo" not in html


def test_pasado_el_limite_se_muestra_el_mensaje_de_la_api():
    limite = ErrorDeApi(429, {"detail": DEMASIADOS})
    with mock.patch("cliente_api.cuentas.solicitar_restablecer_dos_factores", side_effect=limite):
        html = cliente_sin_verificar().post("/segundo-factor/problemas/").content.decode()

    assert 'role="alert"' in html
    assert DEMASIADOS in html


def test_con_la_api_apagada_la_ayuda_lo_dice():
    with mock.patch("cliente_api.cuentas.solicitar_restablecer_dos_factores", side_effect=ApiNoDisponible()):
        html = cliente_sin_verificar().post("/segundo-factor/problemas/").content.decode()

    assert 'role="alert"' in html
    assert MENSAJE_API_NO_DISPONIBLE in html


def test_abrir_el_enlace_del_correo_no_quita_nada_hasta_confirmar():
    # Sin sesión: el correo se puede abrir en otro equipo.
    with mock.patch("cliente_api.cuentas.restablecer_dos_factores") as api:
        respuesta = Client().get(ENLACE)

    api.assert_not_called()
    assert respuesta.status_code == 200
    assert "Quitar la verificación en dos pasos</button>" in respuesta.content.decode()


def test_al_confirmar_viajan_el_uid_y_el_token_y_se_cierra_la_sesion():
    cliente = cliente_sin_verificar()
    with mock.patch("cliente_api.cuentas.restablecer_dos_factores") as api:
        respuesta = cliente.post(ENLACE)

    assert api.call_args.args[1:] == ("MTIz", "abc-123")
    assert respuesta["Location"] == "/?segundo_factor_restablecido=1"
    # La API cerró todas las sesiones de la cuenta: la de este navegador también se cierra.
    assert "token_api" not in cliente.session


def test_un_enlace_vencido_se_avisa_y_la_sesion_sigue_abierta():
    cliente = cliente_sin_verificar()
    vencido = ErrorDeApi(400, {"detail": VENCIDO})
    with mock.patch("cliente_api.cuentas.restablecer_dos_factores", side_effect=vencido):
        html = cliente.post(ENLACE).content.decode()

    assert 'role="alert"' in html
    assert VENCIDO in html
    assert "token_api" in cliente.session


def test_despues_de_quitarla_el_ingreso_lo_confirma():
    aviso = "Quitamos la verificación en dos pasos. Inicia sesión y configúrala de nuevo."

    assert aviso in Client().get("/?segundo_factor_restablecido=1").content.decode()
    assert aviso not in Client().get("/").content.decode()
