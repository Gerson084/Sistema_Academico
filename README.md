# Sistema Académico

Una aplicación Flask para gestionar un sistema académico con base de datos MySQL.

## 🚀 Configuración del Proyecto

### Prerrequisitos
- Python 3.7 o superior
- pip (administrador de paquetes de Python)

### Instalación

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/Gerson084/Sistema_Academico.git
   cd Sistema_Academico
   ```

2. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura las variables de entorno:**
   
   Copia el archivo de ejemplo y configúralo:
   ```bash
   copy .env.example .env
   ```
   
   Edita el archivo `.env` con tus credenciales de base de datos:
   ```env
   # Para desarrollo local
   DATABASE_URI=mysql+pymysql://root:@localhost/sistema_academico
   
   # Para producción (Railway u otro hosting)
   DATABASE_URI=mysql+pymysql://usuario:password@host:puerto/nombre_db
   
   # Otras configuraciones
   SECRET_KEY=genera_una_clave_secreta_aleatoria
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

4. **Ejecuta la aplicación:**
   ```bash
   python app.py
   ```

5. **Prueba la aplicación:**
   - Página principal: http://127.0.0.1:5000/
   - Prueba de conexión BD: http://127.0.0.1:5000/test-db

## 📁 Estructura del Proyecto

```
Sistema_Academico/
├── app.py              # Aplicación principal Flask
├── requirements.txt    # Dependencias del proyecto
├── .env               # Variables de entorno (no incluido en git)
├── .env.example       # Ejemplo de configuración
├── .gitignore         # Archivos ignorados por git
└── db/                # Módulo de base de datos
    ├── __init__.py    # Inicialización del paquete
    └── cn.py          # Configuración de conexión a BD
```

## 🔧 Configuración de Base de Datos

El proyecto utiliza MySQL como base de datos. La configuración se maneja a través de variables de entorno para mayor seguridad.

### Variable de Entorno Principal:
- `DATABASE_URI`: URI completa de conexión a la base de datos
  - **Formato**: `mysql+pymysql://usuario:password@host:puerto/nombre_db`
  - **Desarrollo local**: `mysql+pymysql://root:@localhost/sistema_academico`
  - **Producción (Railway)**: `mysql+pymysql://root:password@host.railway.app:puerto/sistema_academico`

### Otras Variables Requeridas:
- `SECRET_KEY`: Clave secreta de Flask (genera una aleatoria y segura)
- `FLASK_ENV`: Entorno de ejecución (`development` o `production`)
- `FLASK_DEBUG`: Modo debug (`True` o `False`)

### Ejemplo de Configuración en Railway:

Cuando despliegues en Railway, agrega la variable de entorno en el dashboard:

```
DATABASE_URI=mysql+pymysql://root:TU_PASSWORD@host.railway.app:PUERTO/sistema_academico
SECRET_KEY=tu_clave_secreta_super_segura_aqui
FLASK_ENV=production
FLASK_DEBUG=False
```

## 📦 Dependencias Principales

- **Flask**: Framework web de Python
- **Flask-SQLAlchemy**: ORM para Flask
- **PyMySQL**: Driver de MySQL para Python
- **python-dotenv**: Manejo de variables de entorno

## 🚦 Estados de la Aplicación

- ✅ **Conexión a base de datos**: Configurada con Railway MySQL
- ✅ **Variables de entorno**: Implementadas para seguridad
- ✅ **Estructura modular**: Separación de configuración de BD

## 👥 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT.