from flask import Flask, render_template, request, jsonify
from collections import deque
import math

app = Flask(__name__)

class Proceso:
    def __init__(self, pid, llegada, rafagas):
        self.pid = pid
        self.llegada = llegada
        # rafagas es una lista de diccionarios
        self.rafagas = rafagas 
        self.ptr_rafaga = 0 # Apunta a la ráfaga actual (0=CPU inicial, 1=IO, 2=CPU, etc)
        
        self.tiempo_restante_actual_rafaga = rafagas[0]['valor']
        self.estado = 'LISTO' 
        self.tiempo_inicio_primera_vez = -1
        self.tiempo_finalizacion = 0
        self.tiempo_total_io = sum(r['valor'] for r in rafagas if r['tipo'] == 'IO')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simular', methods=['POST'])
def simular():
    data = request.json
    quantum_ms = int(data['quantum']) 
    intercambio = int(data['intercambio'])
    procesos_input = data['procesos']
    
    procesos = []
    for p in procesos_input:
        rafagas_procesadas = []
        # Convertir a ms según la secuencia de quantums ingresada
        for i, valor_q in enumerate(p['secuencia_quantums']):
            valor_ms = int(valor_q) * quantum_ms 
            tipo = 'CPU' if i % 2 == 0 else 'IO'
            rafagas_procesadas.append({'tipo': tipo, 'valor': valor_ms})
            
        procesos.append(Proceso(p['pid'], int(p['llegada']), rafagas_procesadas))

    procesos.sort(key=lambda x: x.llegada)
    
    tiempo_actual = 0
    cola_listos = deque()
    
    gantt = [] 
    trace = [] # AQUÍ GUARDAREMOS LA VISUALIZACIÓN DE LA COLA
    
    procesos_completados = []
    procesos_activos = list(procesos)
    procesos_bloqueados = [] 

    proceso_en_cpu = None
    tiempo_restante_quantum = 0
    
    # --- BUCLE DEL RELOJ ---
    while len(procesos_completados) < len(procesos_input):
        
        # 1. Verificar llegadas
        for p in procesos_activos[:]:
            if p.llegada <= tiempo_actual:
                cola_listos.append(p)
                procesos_activos.remove(p)

        # 2. Verificar retornos de IO
        bloqueados_restantes = []
        for p, retorno in procesos_bloqueados:
            if retorno <= tiempo_actual:
                cola_listos.append(p) 
            else:
                bloqueados_restantes.append((p, retorno))
        procesos_bloqueados = bloqueados_restantes

        # 3. Asignar CPU (Si está libre)
        if not proceso_en_cpu and cola_listos:
            proceso_en_cpu = cola_listos.popleft()
            
            if proceso_en_cpu.tiempo_inicio_primera_vez == -1:
                proceso_en_cpu.tiempo_inicio_primera_vez = tiempo_actual

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

        # 4. Procesar CPU
        if proceso_en_cpu:
            proceso_en_cpu.tiempo_restante_actual_rafaga -= 1
            tiempo_restante_quantum -= 1
            
            se_acabo_rafaga = proceso_en_cpu.tiempo_restante_actual_rafaga <= 0
            se_acabo_quantum = tiempo_restante_quantum <= 0

            if se_acabo_rafaga:
                # Actualizar Gantt
                if gantt and gantt[-1]['pid'] == proceso_en_cpu.pid:
                     gantt[-1]['fin'] = tiempo_actual + 1 

                proceso_en_cpu.ptr_rafaga += 1 
                
                # Verificar si quedan más ráfagas
                if proceso_en_cpu.ptr_rafaga >= len(proceso_en_cpu.rafagas):
                    # TERMINADO
                    proceso_en_cpu.tiempo_finalizacion = tiempo_actual + 1
                    procesos_completados.append(proceso_en_cpu)
                    proceso_en_cpu = None
                else:
                    # Toca IO
                    rafaga_io = proceso_en_cpu.rafagas[proceso_en_cpu.ptr_rafaga]
                    proceso_en_cpu.ptr_rafaga += 1 
                    
                    if proceso_en_cpu.ptr_rafaga < len(proceso_en_cpu.rafagas):
                        proceso_en_cpu.tiempo_restante_actual_rafaga = proceso_en_cpu.rafagas[proceso_en_cpu.ptr_rafaga]['valor']
                    
                    tiempo_regreso = (tiempo_actual + 1) + rafaga_io['valor']
                    procesos_bloqueados.append((proceso_en_cpu, tiempo_regreso))
                    proceso_en_cpu = None
                
                # Context Switch
                if (cola_listos or proceso_en_cpu is None) and len(procesos_completados) < len(procesos_input):
                     tiempo_actual += 1 
                     gantt.append({'pid': 'CTX', 'inicio': tiempo_actual, 'fin': tiempo_actual + intercambio, 'tipo': 'CTX'})
                     tiempo_actual += intercambio - 1 

            elif se_acabo_quantum:
                if gantt and gantt[-1]['pid'] == proceso_en_cpu.pid:
                     gantt[-1]['fin'] = tiempo_actual + 1

                cola_listos.append(proceso_en_cpu)
                proceso_en_cpu = None
                
                tiempo_actual += 1
                gantt.append({'pid': 'CTX', 'inicio': tiempo_actual, 'fin': tiempo_actual + intercambio, 'tipo': 'CTX'})
                tiempo_actual += intercambio - 1

        tiempo_actual += 1
        if tiempo_actual > 10000: break 

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