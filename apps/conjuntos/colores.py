"""Paleta de un color propio (HU-21).

Los ocho acentos del catálogo traen su paleta hecha en design-system/tokens/. Un color propio
no: aquí se sacan de él los mismos cinco tonos que usa la interfaz, mezclándolo con blanco o
negro. No se corrige el color elegido: si es muy claro, la pantalla solo advierte que el texto
blanco de los botones se va a leer con dificultad.
"""
import re

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
CONTRASTE_MINIMO = 4.5  # WCAG AA para texto normal


def es_hex(valor):
    return isinstance(valor, str) and bool(HEX.match(valor))


def a_rgb(hex_):
    return tuple(int(hex_[i : i + 2], 16) for i in (1, 3, 5))


def a_hex(rgb):
    return "#" + "".join(f"{round(canal):02x}" for canal in rgb)


def mezclar(color, con, cantidad):
    """El color movido hacia `con` en la proporción `cantidad` (0 = igual, 1 = `con`)."""
    return tuple(canal + (otro - canal) * cantidad for canal, otro in zip(color, con))


def rampa(hex_):
    """Las variables --acento-* que reemplazan a las del catálogo, con los mismos nombres."""
    color = a_rgb(hex_)
    r, g, b = color
    return {
        "acento-50": a_hex(mezclar(color, BLANCO, 0.9)),
        "acento-600": a_hex(color),
        "acento-700": a_hex(mezclar(color, NEGRO, 0.2)),
        "acento-900": a_hex(mezclar(color, NEGRO, 0.6)),
        "acento-anillo": f"rgba({r},{g},{b},.32)",
    }


def luminancia(hex_):
    def lineal(canal):
        canal /= 255
        return canal / 12.92 if canal <= 0.04045 else ((canal + 0.055) / 1.055) ** 2.4

    r, g, b = (lineal(canal) for canal in a_rgb(hex_))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(uno, otro):
    claro, oscuro = sorted((luminancia(uno), luminancia(otro)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def contraste_con_blanco(hex_):
    """Contraste del texto blanco de los botones (--acento-tinta) sobre el color."""
    return contraste("#ffffff", hex_)


def poco_legible(hex_):
    return es_hex(hex_) and contraste_con_blanco(hex_) < CONTRASTE_MINIMO
