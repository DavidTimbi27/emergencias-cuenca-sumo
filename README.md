# Reto: Accidentes Bus–Moto y Ambulancias en Cuenca (SUMO+TraCI)

Este repositorio contiene la solución completa al reto académico de modelado de tráfico y respuesta de emergencias médicas para la ciudad de Cuenca. El proyecto implementa una simulación microscópica utilizando **SUMO** (Simulation of Urban MObility) controlada mediante la API **TraCI** en Python.

## Descripción del Escenario
El sistema emula 3 horas de tráfico urbano continuo con 4800 vehículos (automóviles, autobuses y motocicletas). Una directiva clave del diseño es que el **teleporting se encuentra deshabilitado** (`time-to-teleport="-1"`), lo que fuerza a la red a acumular colas físicas reales y bloqueos (gridlocks) ante cualquier incidente. 

Mediante control por TraCI (`setSpeedMode(0)`), se vulnera el modelo de seguimiento seguro de Krauss para provocar colisiones por alcance entre autobuses y motocicletas. Al registrarse un accidente, un algoritmo de despacho basado en el **algoritmo de Dijkstra** calcula la ruta óptima en tiempo real (`travelTime`) para enviar ambulancias desde la red de hospitales públicos y privados de la ciudad, evaluando tiempos de respuesta y la reubicación dinámica de la flota.

## Estructura de Archivos del Repositorio
* `cuenca_ciudad.net.xml`: Red vial podada y optimizada de la ciudad de Cuenca.
* `reto.sumocfg`: Archivo de configuración maestro de la simulación SUMO.
* `reto_ambulancias.py`: Script principal en Python que orquesta la simulación, genera los accidentes por TraCI y gestiona el despacho y retorno de las ambulancias.
* `analisis.py`: Script de procesamiento de datos con Pandas y Matplotlib para la obtención de métricas estadísticas y la generación de gráficos.
* `*.csv` y `*.xml`: Archivos de registro, salidas de viajes y flujos vehiculares de la corrida completa.
* `RA_fig_*.png`: Gráficos de alta resolución (300 DPI) que respaldan el análisis técnico.

## Instrucciones de Ejecución
1. Asegúrate de contar con un entorno compatible con SUMO y las librerías de Python (`traci`, `sumolib`, `pandas`, `matplotlib`).
2. Ejecutar la simulación en consola o con interfaz gráfica:
   ```bash
   python3 reto_ambulancias.py
