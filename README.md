# Simulador de Planificación de CPU - Round Robin

Este proyecto es una herramienta web interactiva diseñada para simular y visualizar el comportamiento del algoritmo de planificación de CPU **Round Robin (RR)**, contemplando tiempos de intercambio de contexto (Context Switch) y ráfagas de Entrada/Salida.

---

## 📋 Información Académica

* **Programa Académico:** Ingeniería Informática
* **Universidad:** Politénico Colombiano Jaime Isaza Cadavid
* **Facultad::** Facultad de Ingeniería
* **Programa Académico:** Ingeniería Informática
* **Asignatura:** Sistemas Operativos
* **Docente:** Jhon Jairo Arango Tobón
* **Estudiante:** León Ángel Chancí Guzmán
* **Año:** 2025
---

## 🛠️ Tecnologías Utilizadas

El proyecto implementa una arquitectura Cliente-Servidor ligera:

* **Backend:** Python 3 (Framework **Flask**) para la lógica del algoritmo y cálculos matemáticos.
* **Frontend:** HTML5, CSS3 (Diseño limpio y responsivo) y JavaScript (Fetch API para comunicación asíncrona).
* **Estructuras de Datos:** Uso de colas (`deque`) para la gestión eficiente de procesos listos y ráfagas.

---

## 🚀 Características del Simulador

1.  **Configuración Global:** Permite definir el tamaño del *Quantum* y el tiempo de *Intercambio* (Context Switch) en milisegundos.
2.  **Manejo de Ráfagas Mixtas:** Soporta procesos con secuencias alternadas de CPU y E/S.
3.  **Diagrama de Gantt:** Visualización gráfica de la línea de tiempo, diferenciando ejecuciones de CPU (Azul) y tiempos de intercambio (Rojo).
4.  **Traza de la Cola de Listos:** Visualización paso a paso de cómo los procesos consumen sus Quantums y rotan en la cola, utilizando código de colores por fases de ejecución.
5.  **Cálculos Automáticos:** Genera una tabla con tiempos de llegada, finalización, retorno ($TV$) y espera ($TW$), junto con sus promedios.

---

## 📖 Guía de Uso

## 1. Clonar el repositorio
```
git clone https://github.com/LeonChanci/Round_Robin_SO
```

### 2. Ejecución
Asegúrate de tener Python y Flask instalados.
```bash
pip install flask
```
```bash
python app.py
```

Abre tu navegador en: http://127.0.0.1:5000

---
## 1. Ingreso de Datos
En la interfaz web encontrarás dos secciones principales:

### Parámetros Generales:
- Tamaño del Quantum (ms): Tiempo máximo de CPU por turno.
- Tiempo de Intercambio (ms): Tiempo perdido al cambiar entre procesos.

### Gestión de Procesos: Para cada proceso (P0, P1, etc.), ingresa:
- Tiempo de Llegada: En milisegundos (ms).
- Secuencia (Quantums): Una lista de números separados por comas que representan la cantidad de Quantums requeridos.

El orden siempre es: CPU, E/S, CPU, E/S...

## 2. Ejemplo: 2, 2, 1 significa:
- 2 Quantums de CPU.
- 2 Quantums de Entrada/Salida.
- 1 Quantum de CPU.


## 3. Interpretación de Resultados
Al presionar "Calcular Round Robin", se desplegarán:

- Gantt: Bloques de tamaño fijo (40px CPU, 30px Intercambio) para fácil lectura.
- Evolución de Cola: Muestra el estado del proceso en cada turno (Cuántos Q entra vs. Cuántos Q le quedan).
1. 🔵 Azul: CPU Inicial.
2. 🟠 Naranja: CPU tras primera E/S.
3. 🟣 Morado: CPU tras segunda E/S.
- Cálculos: Tabla con tiempos de llegada, finalización, retorno ($TV$) y espera ($TW$), junto con sus promedios.

## 📂 Estructura del Proyecto

```
/Round_Robin_SO
│
├── app.py                # Lógica del servidor y algoritmo RR
├── README.md             # Documentación del proyecto
└── templates
    └── index.html        # Interfaz de usuario (HTML/JS/CSS)
```

## 👨‍💻 Autor
León Ángel Chancí Guzmán

Estudiante de Ingeniería Informática

Politécnico Colombiano Jaime Isaza Cadavid