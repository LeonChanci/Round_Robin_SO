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
5.  **Cálculos Automáticos:** Genera una tabla con tiempos de llegada, finalización, retorno ($TV$) y espera ($W$), junto con sus promedios.

---

## 📖 Guía de Uso

### 1. Ejecución
Asegúrate de tener Python y Flask instalados.
```bash
pip install flask
python app.py