# Proyecto WEB Torneos

Sistema académico de inscripción a torneos de BJJ, desarrollado con Django y PostgreSQL.

## Preparar el entorno local

1. Crear y activar un entorno virtual:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Instalar dependencias:

   ```powershell
   py -m pip install -r requirements.txt
   ```

3. Crear `.env` a partir de `.env.example`, completar las variables de PostgreSQL y reemplazar `SECRET_KEY` por una clave generada localmente:

   ```powershell
   Copy-Item .env.example .env
   py -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

4. Crear la base de datos PostgreSQL indicada en `.env` y aplicar las migraciones:

   ```powershell
   py manage.py migrate
   py manage.py runserver
   ```

No se deben subir `.env`, el entorno virtual ni copias de la base de datos. Git conserva el código y las migraciones, no los registros de PostgreSQL. Para respaldarlos por separado, con `pg_dump` instalado se puede crear un archivo fuera del proyecto (solicita la contraseña sin incluirla en el comando):

```powershell
pg_dump -Fc -h localhost -p 5432 -U usuario -d base_de_datos -f "$env:USERPROFILE\Documents\torneos.backup"
```

El proyecto incluye los modelos y sus migraciones. Las rutas de la aplicación aún se limitan al panel de administración de Django; no hay pagos, llaves ni resultados.
