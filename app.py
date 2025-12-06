from flask import Flask, render_template, request, jsonify
from collections import deque
import math

app = Flask(__name__)

class Proceso:
    def __init__(self, pid, llegada, rafagas):
        self.pid = pid # Es el Identificador del Proceso
        self.llegada = llegada # Tiempo de llegada del proceso
        self.rafagas = rafagas # Lo que pide el proceso en Quantum -> Lista de ráfagas CPU -> E/S -> CPU -> E/S -> CPU
        self.ptr_rafaga = 0 # Índice o puntero de la ráfaga actual -> Apunta a la ráfaga actual (0=CPU inicial, 1=IO, 2=CPU, etc)
        
        self.tiempo_restante_actual_rafaga = rafagas[0]['valor'] # Contador Regresivo -> Tiempo restante de la ráfaga actual
        self.estado = 'LISTO' # Estado actual del proceso (LISTO, EJECUTANDO, BLOQUEADO, TERMINADO)
        self.tiempo_inicio_primera_vez = -1 # Tiempo en que el proceso se ejecuta por primera vez (-1 = no se ha ejecutado aún)
        self.tiempo_finalizacion = 0 # Tiempo en que el proceso termina su ejecución

        # Cálculo de tiempos = Tiempo de Vuelta ($TV = Fin - Inicio - Total\_IO$)
        self.tiempo_total_io = sum(r['valor'] for r in rafagas if r['tipo'] == 'IO') # Suma todos los tiempos de E/S (Entrada/Salida) que tiene el proceso

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simular', methods=['POST'])
def simular():

    # FASE 1 = Preparación y Traducción
    data = request.json
    quantum_ms = int(data['quantum']) 
    intercambio = int(data['intercambio'])
    procesos_input = data['procesos']
    
    procesos = []
    # Bucle for de conversión:
    for p in procesos_input:
        rafagas_procesadas = []
        # Convertir a ms según la secuencia de quantums ingresada
        for i, valor_q in enumerate(p['secuencia_quantums']):
            # conversión de unidades
            valor_ms = int(valor_q) * quantum_ms # Multiplicamos por el quantum para obtener ms 
            tipo = 'CPU' if i % 2 == 0 else 'IO' # Índices pares = CPU, Impares = IO
            rafagas_procesadas.append({'tipo': tipo, 'valor': valor_ms})
            
        procesos.append(Proceso(p['pid'], int(p['llegada']), rafagas_procesadas))

    # Ordena a los procesos por orden de llegada. Fundamental para saber quién se procesa primero
    procesos.sort(key=lambda x: x.llegada)
    
    tiempo_actual = 0
    cola_listos = deque()
    
    gantt = [] # Se usará para la visualización del diagrama de Gantt
    trace = [] # Se usará para la visualización de la cola de listos
    
    procesos_completados = []
    procesos_activos = list(procesos)
    procesos_bloqueados = [] 

    proceso_en_cpu = None
    tiempo_restante_quantum = 0
    
    # FASE 2 = Gestion de colas
    # --- BUCLE DEL RELOJ ---
    while len(procesos_completados) < len(procesos_input): # Mientras no se hayan completado todos los procesos
        
        # Verificar llegadas nuevas para validar si entran a la cola de listos
        for p in procesos_activos[:]:
            if p.llegada <= tiempo_actual: # si el tiempo de llegada es menor o igual al tiempo actual   
                cola_listos.append(p) # Agregar a la cola de listos
                procesos_activos.remove(p) # Quitar de los procesos activos

        # Verificar retornos de IO - Están los procesos que se fueron a hacer E/S. 
        bloqueados_restantes = []
        for p, retorno in procesos_bloqueados: # Recorremos los procesos bloqueados
            if retorno <= tiempo_actual: # Se valida si ya terminó su E/S
                cola_listos.append(p) # Regresa a la cola de listos
            else: # Si no ha terminado su E/S, sigue bloqueado
                bloqueados_restantes.append((p, retorno)) # Se mantiene en la lista de bloqueados
        procesos_bloqueados = bloqueados_restantes
 

        # FASE 3 = La Asignación de CPU

        # Solo asignamos CPU si está vacía Y hay alguien esperando.
        if not proceso_en_cpu and cola_listos: # Si no hay proceso en CPU y hay procesos en la cola de listos

            # FIFO. popleft() saca al primero de la fila. En Round Robin, el que lleva más tiempo esperando es el siguiente en pasar.
            proceso_en_cpu = cola_listos.popleft()
            
            if proceso_en_cpu.tiempo_inicio_primera_vez == -1: # Si es la primera vez que se ejecuta
                proceso_en_cpu.tiempo_inicio_primera_vez = tiempo_actual # Se registra el tiempo de inicio

            # Reinicio del Cronómetro. Cada vez que un proceso sube a la CPU se le da un Quantum para que lo gaste.
            tiempo_restante_quantum = quantum_ms
            
            # --- REGISTRAR TRAZA (COLA DE LISTOS VISUAL) ---
            # Calculamos cuántos quantums tiene AHORA y cuántos le quedarán
            q_actuales_ms = proceso_en_cpu.tiempo_restante_actual_rafaga
            q_actuales_num = math.ceil(q_actuales_ms / quantum_ms)
            q_restantes_num = q_actuales_num - 1
            if q_restantes_num < 0: q_restantes_num = 0

            # Indice para el color (0=Inicio, 2=Par 1, 4=Par 2...)
            fase_color = proceso_en_cpu.ptr_rafaga 

            trace.append({
                'pid': proceso_en_cpu.pid,
                'entra': q_actuales_num,
                'sale': q_restantes_num,
                'fase': fase_color
            })

            gantt.append({
                'pid': proceso_en_cpu.pid,
                'inicio': tiempo_actual,
                'fin': tiempo_actual, 
                'tipo': 'CPU'
            })

        # FASE 4 = Ejecución y Toma de Decisiones
        if proceso_en_cpu:
            # Restamos 1 ms a la tarea actual que está ejecutando el proceso.
            proceso_en_cpu.tiempo_restante_actual_rafaga -= 1
            # Restamos 1 ms al "cheque" de tiempo (Quantum) que le dimos.
            tiempo_restante_quantum -= 1
            
            # Verificamos si la tarea de CPU llegó a 0 (terminó voluntariamente).
            se_acabo_rafaga = proceso_en_cpu.tiempo_restante_actual_rafaga <= 0

            # Verificamos si el Quantum llegó a 0 (se le acabó el tiempo asignado).
            se_acabo_quantum = tiempo_restante_quantum <= 0

            # CASO A: El proceso terminó su ráfaga de CPU antes de que se acabara su tiempo (Quantum)
            if se_acabo_rafaga:

                # Actualizamos el diagrama de Gantt para cerrar el bloque visual en este ms.
                if gantt and gantt[-1]['pid'] == proceso_en_cpu.pid:
                     gantt[-1]['fin'] = tiempo_actual + 1 

                proceso_en_cpu.ptr_rafaga += 1  # Avanzamos el puntero a la siguiente tarea (que sería una E/S).
                
                # Verificamos si ya no quedan más tareas en su lista (Proceso Finalizado).
                if proceso_en_cpu.ptr_rafaga >= len(proceso_en_cpu.rafagas):
                    proceso_en_cpu.tiempo_finalizacion = tiempo_actual + 1 # Registramos la hora final de salida (+1 para cerrar el ciclo actual).
                    procesos_completados.append(proceso_en_cpu) # Movemos el proceso a la lista de completados.
                    proceso_en_cpu = None # Liberamos la CPU (la variable queda vacía).
                else:
                    # Si quedan tareas, significa que le toca ir a Entrada/Salida (E/S).
                    rafaga_io = proceso_en_cpu.rafagas[proceso_en_cpu.ptr_rafaga]
                    proceso_en_cpu.ptr_rafaga += 1  # Avanzamos puntero otra vez para dejarlo listo en la siguiente CPU.
                    
                    # Pre-cargamos la duración de la próxima ráfaga de CPU (si existe).
                    if proceso_en_cpu.ptr_rafaga < len(proceso_en_cpu.rafagas):
                        proceso_en_cpu.tiempo_restante_actual_rafaga = proceso_en_cpu.rafagas[proceso_en_cpu.ptr_rafaga]['valor']
                    
                    tiempo_regreso = (tiempo_actual + 1) + rafaga_io['valor'] # Calculamos la hora exacta en la que volverá de la E/S.
                    procesos_bloqueados.append((proceso_en_cpu, tiempo_regreso)) # Lo mandamos a la lista de bloqueados con su boleto de regreso.
                    proceso_en_cpu = None # Liberamos la CPU.
                
                # Gestión del Intercambio (Context Switch) al salir voluntariamente.
                if (cola_listos or proceso_en_cpu is None) and len(procesos_completados) < len(procesos_input):
                     tiempo_actual += 1  # Avanzamos el reloj para simular el costo del cambio.
                     gantt.append({'pid': 'CTX', 'inicio': tiempo_actual, 'fin': tiempo_actual + intercambio, 'tipo': 'CTX'}) # Dibujamos el bloque rojo (CTX) en el diagrama.
                     tiempo_actual += intercambio - 1  # Sumamos el resto del tiempo de intercambio (-1 ajuste de bucle).

            # CASO B: EXPROPIACIÓN. No terminó tarea, pero se le acabó el Quantum.
            elif se_acabo_quantum:
                # Cerramos el bloque visual en el Gantt.
                if gantt and gantt[-1]['pid'] == proceso_en_cpu.pid:
                     gantt[-1]['fin'] = tiempo_actual + 1

                cola_listos.append(proceso_en_cpu) # Como no terminó, lo enviamos al FINAL de la cola de listos (Round Robin).
                proceso_en_cpu = None # Liberamos la CPU.
                
                tiempo_actual += 1 # Avanzamos reloj y dibujamos el bloque rojo de Intercambio.
                gantt.append({'pid': 'CTX', 'inicio': tiempo_actual, 'fin': tiempo_actual + intercambio, 'tipo': 'CTX'})
                tiempo_actual += intercambio - 1

       
        tiempo_actual += 1  # El reloj del sistema avanza 1 milisegundo en cada vuelta.
        if tiempo_actual > 10000: break  # Freno de emergencia por si el bucle se vuelve infinito.

    # --- RESULTADOS ---
    resultados = []
    suma_tv = 0
    suma_w = 0
    
    for p in procesos_completados:
        tv = p.tiempo_finalizacion - p.tiempo_total_io - p.llegada
        w = p.tiempo_inicio_primera_vez - p.llegada
        if w < 0: w = 0 
        suma_tv += tv
        suma_w += w
        resultados.append({
            'pid': p.pid,
            'llegada': p.llegada,
            'fin': p.tiempo_finalizacion,
            'io_total': p.tiempo_total_io,
            'primera_vez': p.tiempo_inicio_primera_vez,
            'tv': tv,
            'w': w
        })
        
    resultados.sort(key=lambda x: int(x['pid'][1:])) 
    
    promedio_tv = suma_tv / len(resultados) if resultados else 0
    promedio_w = suma_w / len(resultados) if resultados else 0

    return jsonify({
        'gantt': gantt,
        'trace': trace, 
        'tabla': resultados,
        'promedios': {'tv': round(promedio_tv, 2), 'w': round(promedio_w, 2)}
    })

if __name__ == '__main__':
    app.run(debug=True)