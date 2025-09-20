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
   DB_HOST=tu_host_aqui
   DB_PORT=tu_puerto_aqui
   DB_USER=tu_usuario_aqui
   DB_PASSWORD=tu_password_aqui
   DB_NAME=tu_base_de_datos_aqui
   SECRET_KEY=genera_una_clave_secreta_aleatoria
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

### Variables de Entorno Requeridas:
- `DB_HOST`: Host de la base de datos
- `DB_PORT`: Puerto de la base de datos  
- `DB_USER`: Usuario de la base de datos
- `DB_PASSWORD`: Contraseña de la base de datos
- `DB_NAME`: Nombre de la base de datos
- `SECRET_KEY`: Clave secreta de Flask

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