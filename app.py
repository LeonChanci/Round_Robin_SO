from flask import Flask, render_template, request, jsonify
from collections import deque

app = Flask(__name__)

class Proceso:
    def __init__(self, pid, llegada, rafagas):
        self.pid = pid
        self.llegada = llegada
        # rafagas es una lista de diccionarios: [{'tipo': 'CPU', 'valor': 200}, ...]
        self.rafagas = deque(rafagas) 
        self.estado = 'LISTO' 
        self.tiempo_restante_actual = 0
        self.tiempo_inicio_primera_vez = -1
        self.tiempo_finalizacion = 0
        # Calculamos el IO total para las fórmulas finales
        self.tiempo_total_io = sum(r['valor'] for r in rafagas if r['tipo'] == 'IO')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simular', methods=['POST'])
def simular():
    data = request.json
    quantum_ms = int(data['quantum']) # El tamaño del quantum en ms (ej: 100)
    intercambio = int(data['intercambio'])
    procesos_input = data['procesos']
    
    # Configuración inicial
    procesos = []
    for p in procesos_input:
        rafagas_procesadas = []
        
        # PROCESAMIENTO DE LA TABLA:
        # La entrada viene como una lista de números [2, 2, 1, 2, 3] (Quantums)
        # Posiciones pares (0, 2, 4...) son CPU
        # Posiciones impares (1, 3, 5...) son E/S
        
        for i, valor_q in enumerate(p['secuencia_quantums']):
            valor_ms = int(valor_q) * quantum_ms # CONVERSIÓN: Quantum * Tamaño Quantum
            
            tipo = 'CPU' if i % 2 == 0 else 'IO'
            rafagas_procesadas.append({'tipo': tipo, 'valor': valor_ms})
            
        # Nota: La llegada ya viene en milisegundos según tu tabla
        procesos.append(Proceso(p['pid'], int(p['llegada']), rafagas_procesadas))

    # Ordenar por llegada inicial
    procesos.sort(key=lambda x: x.llegada)
    
    tiempo_actual = 0
    cola_listos = deque()
    
    gantt = [] 
    procesos_completados = []
    procesos_activos = list(procesos)
    procesos_bloqueados = [] # [(proceso, tiempo_retorno)]

    proceso_en_cpu = None
    tiempo_restante_quantum = 0
    
    # --- BUCLE DEL RELOJ ---
    while len(procesos_completados) < len(procesos_input):
        
        # 1. Verificar llegadas (Nuevos procesos entran a la cola)
        for p in procesos_activos[:]:
            if p.llegada <= tiempo_actual:
                cola_listos.append(p)
                procesos_activos.remove(p)

        # 2. Verificar retornos de IO (Procesos bloqueados vuelven a cola)
        bloqueados_restantes = []
        for p, retorno in procesos_bloqueados:
            if retorno <= tiempo_actual:
                cola_listos.append(p) 
            else:
                bloqueados_restantes.append((p, retorno))
        procesos_bloqueados = bloqueados_restantes

        # 3. Lógica del Procesador
        if proceso_en_cpu:
            # Decrementar contadores
            proceso_en_cpu.rafagas[0]['valor'] -= 1
            tiempo_restante_quantum -= 1
            
            se_acabo_rafaga = proceso_en_cpu.rafagas[0]['valor'] <= 0
            se_acabo_quantum = tiempo_restante_quantum <= 0

            if se_acabo_rafaga:
                # Terminó la ráfaga actual (sea CPU o lo que fuera, aunque en CPU solo procesamos CPU)
                # Registrar fin en Gantt
                if gantt and gantt[-1]['pid'] == proceso_en_cpu.pid:
                     gantt[-1]['fin'] = tiempo_actual

                proceso_en_cpu.rafagas.popleft() # Sacar la tarea terminada
                
                if not proceso_en_cpu.rafagas:
                    # PROCESO TERMINADO FINALMENTE
                    proceso_en_cpu.tiempo_finalizacion = tiempo_actual
                    procesos_completados.append(proceso_en_cpu)
                    proceso_en_cpu = None
                else:
                    # El proceso pasa a E/S (Siguiente elemento en la lista)
                    rafaga_io = proceso_en_cpu.rafagas.popleft()
                    tiempo_regreso = tiempo_actual + rafaga_io['valor']
                    procesos_bloqueados.append((proceso_en_cpu, tiempo_regreso))
                    proceso_en_cpu = None
                
                # Tiempo de intercambio al salir
                if (cola_listos or proceso_en_cpu is None) and len(procesos_completados) < len(procesos_input):
                     gantt.append({'pid': 'CTX', 'inicio': tiempo_actual, 'fin': tiempo_actual + intercambio, 'tipo': 'CTX'})
                     tiempo_actual += intercambio 
            
            elif se_acabo_quantum:
                # EXPROPIACIÓN (Se acabó el tiempo asignado)
                if gantt and gantt[-1]['pid'] == proceso_en_cpu.pid:
                     gantt[-1]['fin'] = tiempo_actual

                cola_listos.append(proceso_en_cpu) # Vuelve al final de la cola
                proceso_en_cpu = None
                
                # Registrar contexto en Gantt
                gantt.append({'pid': 'CTX', 'inicio': tiempo_actual, 'fin': tiempo_actual + intercambio, 'tipo': 'CTX'})
                tiempo_actual += intercambio 

        # 4. Asignar CPU
        if not proceso_en_cpu and cola_listos:
            proceso_en_cpu = cola_listos.popleft()
            
            if proceso_en_cpu.tiempo_inicio_primera_vez == -1:
                proceso_en_cpu.tiempo_inicio_primera_vez = tiempo_actual

            tiempo_restante_quantum = quantum_ms # Reiniciar Quantum completo
            
            gantt.append({
                'pid': proceso_en_cpu.pid,
                'inicio': tiempo_actual,
                'fin': tiempo_actual, 
                'tipo': 'CPU'
            })

        # Avanzar reloj
        # Condición de parada: Si no hay nada ejecutando y ya terminaron todos, salir.
        if len(procesos_completados) == len(procesos_input):
            break
            
        tiempo_actual += 1

    # --- RESULTADOS ---
    resultados = []
    suma_tv = 0
    suma_w = 0
    
    for p in procesos_completados:
        tv = p.tiempo_finalizacion - p.tiempo_total_io - p.llegada
        w = p.tiempo_inicio_primera_vez - p.llegada
        
        # Ajuste para evitar negativos si la llegada es tarde
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
        
    resultados.sort(key=lambda x: int(x['pid'][1:])) # Ordenar P0, P1, P2...
    
    promedio_tv = suma_tv / len(resultados) if resultados else 0
    promedio_w = suma_w / len(resultados) if resultados else 0

    return jsonify({
        'gantt': gantt,
        'tabla': resultados,
        'promedios': {'tv': round(promedio_tv, 2), 'w': round(promedio_w, 2)}
    })

if __name__ == '__main__':
    app.run(debug=True)