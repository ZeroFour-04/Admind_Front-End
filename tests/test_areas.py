"""Pantallas de HU-09: catálogo de áreas comunes y paso de áreas del asistente. La API se simula."""
from unittest import mock

from apps.areas.forms import AreaForm
from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

SALON = {
    "id": "3c4d5e6f-0000-4000-8000-000000000001",
    "nombre": "Salón comunal",
    "descripcion": "",
    "hora_apertura": "08:00",
    "hora_cierre": "22:00",
    "duracion_franja_minutos": 240,
    "aforo_maximo": 50,
    "en_mantenimiento": False,
    "activo": True,
}
PORTERIA = {**SALON, "id": "3c4d5e6f-0000-4000-8000-000000000002", "nombre": "Portería", "en_mantenimiento": True}
DATOS = {
    "nombre": "Salón comunal", "hora_apertura": "08:00", "hora_cierre": "22:00", "duracion_franja_minutos": "240",
    "aforo_maximo": "50",
}
ADMINISTRACION = ["area.ver", "area.gestionar"]


def test_la_lista_muestra_nombre_horario_y_estado():
    with mock.patch("cliente_api.areas.listar", return_value=[SALON, PORTERIA]):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/areas/").content.decode()

    assert "Salón comunal" in html and "Portería" in html
    assert "Clasificación" not in html
    assert "08:00 a 22:00" in html and "aforo 50" in html
    assert "En mantenimiento" in html and "Disponible" in html
    assert "Maqueta" not in html


def test_sin_area_gestionar_no_se_ven_acciones():
    with mock.patch("cliente_api.areas.listar", return_value=[SALON]):
        html = cliente_con_sesion(permisos=["area.ver"]).get("/areas/").content.decode()

    assert "Salón comunal" in html
    assert "Crear área" not in html
    assert "Desactivar" not in html and "Editar" not in html


def test_secretaria_ve_el_boton_solicitudes_sin_acciones_de_edicion():
    permisos = ["area.ver", "reserva.ver_todas", "reserva.aprobar", "reserva.rechazar"]
    with mock.patch("cliente_api.areas.listar", return_value=[SALON]):
        html = cliente_con_sesion(permisos=permisos).get("/areas/").content.decode()

    assert f'href="/reservas/areas/{SALON["id"]}/solicitudes/"' in html
    assert ">Solicitudes</a>" in html
    assert ">Editar</a>" not in html
    assert ">Desactivar</button>" not in html


def test_sin_areas_invita_a_crear_la_primera():
    with mock.patch("cliente_api.areas.listar", return_value=[]):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/areas/").content.decode()

    assert "Todavía no hay áreas comunes" in html
    assert "Crear la primera área" in html


def test_crear_manda_las_horas_como_texto_y_vuelve_a_la_lista():
    with mock.patch("cliente_api.areas.crear", return_value=SALON) as crear:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/areas/nueva/", DATOS)

    assert crear.call_args.args[1] == {
        "nombre": "Salón comunal", "descripcion": "",
        "hora_apertura": "08:00", "hora_cierre": "22:00", "duracion_franja_minutos": 240, "aforo_maximo": 50,
    }
    assert respuesta["Location"] == "/areas/?creada=1"


def test_la_duracion_minima_de_la_franja_es_de_dos_horas():
    menor_al_minimo = AreaForm(data={**DATOS, "duracion_franja_minutos": "119"})
    minimo = AreaForm(data={**DATOS, "duracion_franja_minutos": "120"})

    assert not menor_al_minimo.is_valid()
    assert "duracion_franja_minutos" in menor_al_minimo.errors
    assert minimo.is_valid()


def test_el_formulario_exige_el_aforo():
    sin_aforo = AreaForm(data={**DATOS, "aforo_maximo": ""})
    en_cero = AreaForm(data={**DATOS, "aforo_maximo": "0"})

    assert not sin_aforo.is_valid() and "aforo_maximo" in sin_aforo.errors
    assert not en_cero.is_valid() and "aforo_maximo" in en_cero.errors
    assert AreaForm(data=DATOS).is_valid()


def test_un_400_de_la_api_cae_en_su_campo():
    rechazo = ErrorDeApi(400, {"nombre": ["Ya existe un área con este nombre en el conjunto."]})
    with mock.patch("cliente_api.areas.crear", side_effect=rechazo):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/areas/nueva/", DATOS)

    assert 'id="id_nombre-error">Ya existe un área con este nombre en el conjunto.' in respuesta.content.decode()


def test_editar_manda_el_mantenimiento():
    with (
        mock.patch("cliente_api.areas.obtener", return_value=SALON),
        mock.patch("cliente_api.areas.editar", return_value=SALON) as editar,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/areas/{SALON['id']}/editar/", {**DATOS, "en_mantenimiento": "on"}
        )

    assert editar.call_args.args[2]["en_mantenimiento"] is True
    assert respuesta["Location"] == "/areas/"


def test_desactivar_llama_a_la_api_y_un_409_se_muestra():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with mock.patch("cliente_api.areas.desactivar") as desactivar:
        assert cliente.post(f"/areas/{SALON['id']}/desactivar/")["Location"] == "/areas/"
    desactivar.assert_called_once()

    with (
        mock.patch("cliente_api.areas.desactivar", side_effect=ErrorDeApi(409, {"detail": "El área ya está inactiva."})),
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
    ):
        html = cliente.post(f"/areas/{SALON['id']}/desactivar/").content.decode()
    assert "El área ya está inactiva." in html


def test_el_asistente_tiene_cinco_pasos_y_el_de_areas_crea_en_el_conjunto_activo():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION + ["conjunto.editar"])
    with mock.patch("cliente_api.areas.listar", return_value=[]):
        html = cliente.get("/conjuntos/asistente/areas/").content.decode()
    with mock.patch("cliente_api.areas.crear", return_value=SALON) as crear:
        respuesta = cliente.post("/conjuntos/asistente/areas/", DATOS)

    assert "3. Áreas" in html and "4. Reglas" in html and "5. Resumen" in html
    assert "conjunto" not in crear.call_args.args[1]
    assert respuesta["Location"] == "/conjuntos/asistente/areas/"


def test_el_lateral_muestra_areas_comunes_solo_con_area_gestionar():
    with mock.patch("cliente_api.anuncios.listar", return_value=[]):
        con_permiso = cliente_con_sesion(permisos=ADMINISTRACION).get("/anuncios/").content.decode()
        sin_permiso = cliente_con_sesion(permisos=["area.ver"]).get("/anuncios/").content.decode()

    assert ">Áreas comunes</a>" in con_permiso
    assert ">Áreas comunes</a>" not in sin_permiso
