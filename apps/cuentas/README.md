# cuentas

Alcance: Núcleo (§3.1).

Las pantallas de entrada.

## Qué va aquí

- Ingreso y salida
- Verificación del 2FA TOTP y su activación para quien tiene permisos sensibles
- "¿Problemas con la verificación en dos pasos?": pedir por correo el enlace que quita el 2FA y la pantalla que lo confirma
- Recuperación de contraseña

## Con qué se conecta

- Backend: `Admind_Backend/apps/cuentas/`
- `templates/base/`: la estructura sin sesión
- `apps/conjuntos/`: después de ingresar, el selector de conjunto activo

## Referencias

Maestro §3.1, §5.3 · Sprint 1 (§11.2)

## Pendiente

- Sesión o token con la API (§12.7 b)
