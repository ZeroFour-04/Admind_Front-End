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
    "modo_uso": "reserva",
    "duracion_franja_minutos": 240,
    "permanencia_maxima_minutos": None,
    "aforo_maximo": 50,
    "en_mantenimiento": False,
    "activo": True,
}
GIMNASIO = {
    **SALON,
    "id": "3c4d5e6f-0000-4000-8000-000000000003",
    "nombre": "Gimnasio",
    "modo_uso": "ingreso",
    "duracion_franja_minutos": None,
    "permanencia_maxima_minutos": 60,
    "aforo_maximo": 3,
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
        "modo_uso": "reserva", "nombre": "Salón comunal", "descripcion": "",
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


def test_el_asistente_tiene_siete_pasos_y_el_de_areas_crea_en_el_conjunto_activo():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION + ["conjunto.editar"])
    with mock.patch("cliente_api.areas.listar", return_value=[]):
        html = cliente.get("/conjuntos/asistente/areas/").content.decode()
    with mock.patch("cliente_api.areas.crear", return_value=SALON) as crear:
        respuesta = cliente.post("/conjuntos/asistente/areas/", DATOS)

    assert "4. Áreas" in html and "5. Reglas" in html and "6. Reglamento" in html and "7. Resumen" in html
    assert "conjunto" not in crear.call_args.args[1]
    assert respuesta["Location"] == "/conjuntos/asistente/areas/"


def test_el_lateral_muestra_areas_comunes_solo_con_area_gestionar():
    with mock.patch("cliente_api.anuncios.listar", return_value=[]):
        con_permiso = cliente_con_sesion(permisos=ADMINISTRACION).get("/anuncios/").content.decode()
        sin_permiso = cliente_con_sesion(permisos=["area.ver"]).get("/anuncios/").content.decode()

    assert ">Áreas comunes</a>" in con_permiso
    assert ">Áreas comunes</a>" not in sin_permiso


def test_un_area_tipica_llena_el_formulario_del_asistente_sin_guardar_nada():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION + ["conjunto.editar"])
    with (
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
        mock.patch("cliente_api.areas.crear") as crear,
    ):
        # Los atributos de cada campo van en varias líneas: se dejan en una para buscarlos.
        html = " ".join(cliente.get("/conjuntos/asistente/areas/?plantilla=bbq").content.decode().split())
        sin_plantilla = " ".join(cliente.get("/conjuntos/asistente/areas/?plantilla=piscina").content.decode().split())

    assert 'name="nombre" value="BBQ"' in html and 'name="aforo_maximo" value="15"' in html
    assert 'name="hora_apertura" value="10:00"' in html
    assert '<details class="am-tarjeta tarjeta-contenido" open>' in html
    assert 'href="?plantilla=cancha"' in html
    assert 'name="nombre" value=""' in sin_plantilla
    crear.assert_not_called()


# Modo de uso (plan de zonas con ingreso, F5)

DATOS_DE_INGRESO = {
    "modo_uso": "ingreso", "nombre": "Gimnasio", "hora_apertura": "05:00", "hora_cierre": "22:00",
    "permanencia_maxima_minutos": "60", "aforo_maximo": "3",
}


def test_crear_un_area_con_ingreso_manda_el_modo_y_la_permanencia_sin_duracion():
    with mock.patch("cliente_api.areas.crear", return_value=GIMNASIO) as crear:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/areas/nueva/", DATOS_DE_INGRESO)

    assert crear.call_args.args[1] == {
        "modo_uso": "ingreso", "nombre": "Gimnasio", "descripcion": "",
        "hora_apertura": "05:00", "hora_cierre": "22:00", "permanencia_maxima_minutos": 60, "aforo_maximo": 3,
    }
    assert respuesta["Location"] == "/areas/?creada=1"


def test_cada_modo_exige_su_campo():
    sin_permanencia = AreaForm(data={**DATOS_DE_INGRESO, "permanencia_maxima_minutos": ""})
    permanencia_corta = AreaForm(data={**DATOS_DE_INGRESO, "permanencia_maxima_minutos": "10"})
    sin_duracion = AreaForm(data={**DATOS, "duracion_franja_minutos": ""})

    assert "permanencia_maxima_minutos" in sin_permanencia.errors
    assert "permanencia_maxima_minutos" in permanencia_corta.errors
    assert "duracion_franja_minutos" in sin_duracion.errors
    assert AreaForm(data=DATOS_DE_INGRESO).is_valid()


def test_el_formulario_de_alta_ofrece_los_dos_modos_con_sus_campos_rotulados():
    html = cliente_con_sesion(permisos=ADMINISTRACION).get("/areas/nueva/").content.decode()

    assert 'name="modo_uso" value="reserva"' in html and 'name="modo_uso" value="ingreso"' in html
    assert "Solo para áreas con reserva" in html and "Solo para áreas con ingreso" in html
    assert "El modo no se puede cambiar" in html


def test_editar_no_ofrece_cambiar_el_modo_y_solo_muestra_el_campo_de_su_modo():
    with mock.patch("cliente_api.areas.obtener", return_value=GIMNASIO):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/areas/{GIMNASIO['id']}/editar/").content.decode()
    with mock.patch("cliente_api.areas.obtener", return_value=SALON):
        de_reserva = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/areas/{SALON['id']}/editar/").content.decode()

    assert 'name="modo_uso"' not in html and "<b>Con ingreso</b>" in html
    assert 'name="permanencia_maxima_minutos"' in html and 'name="duracion_franja_minutos"' not in html
    assert 'name="duracion_franja_minutos"' in de_reserva and 'name="permanencia_maxima_minutos"' not in de_reserva


def test_editar_un_area_con_ingreso_manda_la_permanencia_y_no_el_modo():
    with (
        mock.patch("cliente_api.areas.obtener", return_value=GIMNASIO),
        mock.patch("cliente_api.areas.editar", return_value=GIMNASIO) as editar,
    ):
        cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/areas/{GIMNASIO['id']}/editar/", {**DATOS_DE_INGRESO, "permanencia_maxima_minutos": "90"}
        )

    enviado = editar.call_args.args[2]
    assert enviado["permanencia_maxima_minutos"] == 90
    assert "modo_uso" not in enviado and "duracion_franja_minutos" not in enviado


def test_la_tabla_dice_como_se_usa_cada_area():
    with mock.patch("cliente_api.areas.listar", return_value=[SALON, GIMNASIO]):
        html = " ".join(cliente_con_sesion(permisos=ADMINISTRACION).get("/areas/").content.decode().split())

    assert "<td>Salón comunal</td> <td>Con reserva</td>" in html
    assert "<td>Gimnasio</td> <td>Con ingreso</td>" in html
    assert "permanencia de 60 min · aforo 3" in html and "franjas de 240 min · aforo 50" in html


def test_un_400_de_la_api_sobre_la_permanencia_cae_en_su_campo():
    rechazo = ErrorDeApi(400, {"permanencia_maxima_minutos": ["La permanencia máxima es obligatoria en un área con ingreso."]})
    with mock.patch("cliente_api.areas.crear", side_effect=rechazo):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/areas/nueva/", DATOS_DE_INGRESO)

    assert "id_permanencia_maxima_minutos-error" in respuesta.content.decode()
