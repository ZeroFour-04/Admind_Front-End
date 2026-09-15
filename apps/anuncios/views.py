from datetime import date

from django.shortcuts import render

# Maqueta. Un anuncio tiene uno de dos alcances: todo el conjunto o una vivienda (maestro §5.7).
ANUNCIOS_DE_EJEMPLO = [
    {
        "titulo": "Mantenimiento de la piscina",
        "alcance": "Todo el conjunto",
        "publicado": date(2026, 9, 15),
        "texto": "La piscina estará cerrada del lunes 21 al miércoles 23 de septiembre por limpieza y cambio de filtros.",
    },
    {
        "titulo": "Corte de agua programado",
        "alcance": "Todo el conjunto",
        "publicado": date(2026, 9, 14),
        "texto": "La empresa de acueducto suspende el servicio el jueves 17 de septiembre, de 8:00 a. m. a 2:00 p. m. Guarda agua desde la noche anterior.",
    },
    {
        "titulo": "Revisión del medidor de gas",
        "alcance": "Vivienda Torre 3 – 402",
        "publicado": date(2026, 9, 14),
        "texto": "El técnico de la empresa de gas visita el apartamento el viernes 18 de septiembre en la mañana. Deja libre el acceso al medidor.",
    },
]


def lista(request):
    return render(request, "anuncios/lista.html", {"anuncios": ANUNCIOS_DE_EJEMPLO})
