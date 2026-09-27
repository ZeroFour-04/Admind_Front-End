"""Pantallas de HU-09: catálogo de áreas comunes y paso de áreas del asistente. La API se simula."""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

SALON = {
    "id": "3c4d5e6f-0000-4000-8000-000000000001",
    "nombre": "Salón comunal",
    "descripcion": "",
    "clasificacion": "comun",
    "clasificacion_nombre": "Común",
    "es_esencial": False,
    "hora_apertura": "08:00",
    "hora_cierre": "22:00",
    "duracion_franja_minutos": 240,
    "en_mantenimiento": False,
    "activo": True,
}
PORTERIA = {**SALON, "id": "3c4d5e6f-0000-4000-8000-000000000002", "nombre": "Portería",
            "clasificacion": "comun_esencial", "clasificacion_nombre": "Común esencial", "es_esencial": True,
            "en_mantenimiento": True}
DATOS = {"nombre": "Salón comunal", "hora_apertura": "08:00", "hora_cierre": "22:00", "duracion_franja_minutos": "240"}
ADMINISTRACION = ["area.ver", "area.gestionar"]


def test_la_lista_muestra_clasificacion_esencial_horario_y_estado():
    with mock.patch("cliente_api.areas.listar", return_value=[SALON, PORTERIA]):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/areas/").content.decode()

    assert "Salón comunal" in html and "Común esencial" in html
    assert "Esencial</span>" in html
    assert "08:00 a 22:00" in html
    assert "En mantenimiento" in html and "Disponible" in html
    assert "Maqueta" not in html


def test_sin_area_gestionar_no_se_ven_acciones():
    with mock.patch("cliente_api.areas.listar", return_value=[SALON]):
        html = cliente_con_sesion(permisos=["area.ver"]).get("/areas/").content.decode()

    assert "Salón comunal" in html
    assert "Crear área" not in html
    assert "Desactivar" not in html and "Editar" not in html


def test_sin_areas_invita_a_crear_la_primera():
    with mock.patch("cliente_api.areas.listar", return_value=[]):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/areas/").content.decode()

    assert "Todavía no hay áreas comunes" in html
    assert "Crear la primera área" in html


def test_la_clasificacion_es_obligatoria_y_no_viene_marcada():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)

    formulario = cliente.get("/areas/nueva/").content.decode()
    with mock.patch("cliente_api.areas.crear") as crear:
        respuesta = cliente.post("/areas/nueva/", DATOS)

    assert 'name="clasificacion"' in formulario and "checked" not in formulario
    assert "La mora no restringe su uso." in formulario
    crear.assert_not_called()
    assert respuesta.status_code == 200
    assert "Este campo es obligatorio." in respuesta.content.decode()


def test_crear_manda_las_horas_como_texto_y_vuelve_a_la_lista():
    with mock.patch("cliente_api.areas.crear", return_value=SALON) as crear:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/areas/nueva/", {**DATOS, "clasificacion": "comun"}
        )

    assert crear.call_args.args[1] == {
        "nombre": "Salón comunal", "descripcion": "", "clasificacion": "comun",
        "hora_apertura": "08:00", "hora_cierre": "22:00", "duracion_franja_minutos": 240,
    }
    assert respuesta["Location"] == "/areas/?creada=1"


def test_un_400_de_la_api_cae_en_su_campo():
    rechazo = ErrorDeApi(400, {"nombre": ["Ya existe un área con este nombre en el conjunto."]})
    with mock.patch("cliente_api.areas.crear", side_effect=rechazo):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/areas/nueva/", {**DATOS, "clasificacion": "comun"})

    assert 'id="id_nombre-error">Ya existe un área con este nombre en el conjunto.' in respuesta.content.decode()


def test_editar_manda_el_mantenimiento_y_no_la_clasificacion():
    with (
        mock.patch("cliente_api.areas.obtener", return_value=SALON),
        mock.patch("cliente_api.areas.editar", return_value=SALON) as editar,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/areas/{SALON['id']}/editar/", {**DATOS, "en_mantenimiento": "on"}
        )

    assert editar.call_args.args[2]["en_mantenimiento"] is True
    assert "clasificacion" not in editar.call_args.args[2]
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
        respuesta = cliente.post("/conjuntos/asistente/areas/", {**DATOS, "clasificacion": "comun"})

    assert "3. Áreas" in html and "4. Reglas" in html and "5. Resumen" in html
    assert "conjunto" not in crear.call_args.args[1]
    assert respuesta["Location"] == "/conjuntos/asistente/areas/"


def test_el_lateral_muestra_areas_comunes_solo_con_area_gestionar():
    with mock.patch("cliente_api.anuncios.listar", return_value=[]):
        con_permiso = cliente_con_sesion(permisos=ADMINISTRACION).get("/anuncios/").content.decode()
        sin_permiso = cliente_con_sesion(permisos=["area.ver"]).get("/anuncios/").content.decode()

    assert ">Áreas comunes</a>" in con_permiso
    assert ">Áreas comunes</a>" not in sin_permiso
