# Estado de Prisma

Página pública con el estado de Prisma y sus servicios: **https://prisma.is-a.dev**

- Cada 10 minutos, GitHub Actions consulta el `/estado.json` público del panel de Prisma y publica la página en GitHub Pages.
- Vive fuera del servidor a propósito: si el servidor se cae, la página lo sigue mostrando.
- Solo muestra nombre, descripción y estado de cada servicio. Nada personal, sin claves.
