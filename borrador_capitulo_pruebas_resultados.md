# Capítulo: Pruebas y resultados

## 1. Escenario de pruebas

En este capítulo se presentan las pruebas realizadas para comprobar el funcionamiento del simulador y analizar los resultados obtenidos en distintos casos de estudio. Las pruebas se realizan sobre el escenario tridimensional del Centro Universitario de Mérida, utilizando la antena transmisora situada en la posición definida en la escena de simulación.

Para las pruebas base se utiliza una configuración común, manteniendo constantes la frecuencia, el ancho de banda, el tamaño de la rejilla, el tamaño del voxel y las ganancias de los receptores. De esta forma, las diferencias observadas en los resultados pueden atribuirse principalmente al parámetro que se modifica en cada prueba.

La configuración inicial utiliza el modelo FSPL, ya que es el modelo más sencillo de comprobar de forma teórica. Al no depender del escenario, del tipo de entorno ni de pérdidas aleatorias por shadowing, permite validar que el cálculo de distancia, ganancia de antena, pérdidas de propagación y potencia recibida se está realizando correctamente.

Tabla sugerida:

| Parámetro | Valor |
|---|---:|
| Frecuencia | 1.785 GHz |
| Potencia de transmisión base | 30 dBm |
| Potencia de transmisión máxima | 55.44 dBm |
| Ancho de banda | 10 MHz |
| Modelo de pérdidas base | FSPL |
| Ganancia receptor vehicular | 3 dBi |
| Ganancia receptor celular | 0 dBi |
| Tamaño de voxel | 2 m |
| Método base | Vasiliadis, k = 2 |

## 2. Validación del patrón de radiación reconstruido

Antes de analizar la cobertura, se valida la reconstrucción del patrón de radiación. Para ello se compara la matriz de ganancia generada en Unity con los resultados obtenidos mediante un script externo en MATLAB.

La validación se realiza usando el modo debug implementado en el simulador. Este modo permite consultar la ganancia reconstruida para puntos concretos del espacio y comprobar que los valores coinciden con los esperados según los ángulos vertical y horizontal. Además, se crearon esferas de prueba como prefabs dentro de la escena para situarlas en posiciones conocidas de la rejilla y visualizar directamente los valores calculados en cada punto.

La comparación se realiza para distintos métodos de reconstrucción, incluyendo Vasiliadis con distintos valores del factor k. Esto permite comprobar cómo afecta este parámetro a la reconstrucción del patrón y verificar que Unity y MATLAB generan valores coherentes.

Tabla sugerida:

| Método | Parámetro | Ganancia MATLAB (dBi) | Ganancia Unity (dBi) | Error absoluto (dB) |
|---|---:|---:|---:|---:|
| Vasiliadis | k = 1 | X | X | X |
| Vasiliadis | k = 2 | X | X | X |
| Gil | - | X | X | X |

Otra opción es comparar varias direcciones concretas:

| Theta | Phi | MATLAB (dBi) | Unity (dBi) | Error absoluto (dB) |
|---:|---:|---:|---:|---:|
| 90 | 0 | X | X | X |
| 90 | 30 | X | X | X |
| 60 | 0 | X | X | X |

## 3. Validación del cálculo de potencia recibida

Para comprobar que el cálculo de potencia recibida es correcto, se realiza una prueba usando el modelo FSPL. Este modelo permite calcular las pérdidas de propagación de forma directa a partir de la distancia y la frecuencia, por lo que es adecuado para comparar el resultado del simulador con un cálculo teórico.

La pérdida FSPL se calcula mediante:

```text
FSPL(dB) = 32.44 + 20 log10(f_MHz) + 20 log10(d_km)
```

A partir de esta pérdida, la potencia recibida se obtiene mediante:

```text
Prx(dBm) = Ptx(dBm) + Gtx(dBi) + Grx(dBi) - FSPL(dB)
```

Para esta prueba se seleccionan varios puntos de la rejilla mediante las esferas de debug. Para cada punto se obtiene la distancia al transmisor, la ganancia de transmisión asociada a la dirección del punto y la potencia recibida calculada por el simulador. Después se compara con el valor teórico obtenido manualmente.

Tabla sugerida:

| Punto | Distancia (m) | Gtx (dBi) | FSPL teórico (dB) | Prx teórica (dBm) | Prx simulador (dBm) | Error (dB) |
|---|---:|---:|---:|---:|---:|---:|
| Debug 1 | X | X | X | X | X | X |
| Debug 2 | X | X | X | X | X | X |
| Debug 3 | X | X | X | X | X | X |

## 4. Resultados de cobertura en la rejilla tridimensional

En este apartado se analizan los mapas de calor generados sobre la rejilla tridimensional. Estos mapas permiten observar cómo se distribuye la potencia recibida en el volumen del escenario, teniendo en cuenta la posición de la antena, el patrón de radiación, la distancia al transmisor y las pérdidas adicionales por edificios.

Primero se muestran los resultados obtenidos con la configuración base. En esta prueba se observa cómo la potencia recibida disminuye al alejarse del transmisor y cómo la forma del patrón de radiación afecta a la distribución espacial de la señal.

Después se analiza el efecto del umbral de visualización. Al modificar este umbral, se ocultan las zonas de menor potencia y se facilita la observación de las regiones con mejor cobertura. Esto es útil porque, al representar muchos voxeles semitransparentes al mismo tiempo, el mapa puede saturarse visualmente.

Figuras sugeridas:

- Mapa 3D con umbral bajo
- Mapa 3D con umbral alto
- Mapa 2D por capas cerca de la altura de la antena
- Mapa 2D a otra altura

## 5. Resultados de receptores móviles

En este apartado se analizan los resultados obtenidos para los tres receptores móviles: el vehículo del campus, el vehículo lineal y el peatón. Cada receptor sigue una ruta distinta, lo que permite observar cómo varían la potencia recibida y la SNR en diferentes situaciones del escenario.

Para cada receptor se generan archivos CSV con las muestras registradas durante el recorrido. A partir de estos datos se obtienen las gráficas de potencia recibida frente a distancia, SNR frente a distancia y SNR frente al tiempo.

### Vehículo del campus

El vehículo del campus realiza un recorrido cerrado alrededor de la escena. Este receptor permite analizar cómo cambia la señal en un desplazamiento amplio, pasando por zonas con diferentes distancias, orientaciones respecto a la antena y posibles obstáculos entre transmisor y receptor.

### Vehículo lineal

El vehículo lineal permite analizar la evolución de la señal de forma más controlada. Al seguir un recorrido más directo, resulta útil para observar tendencias en la potencia recibida y en la SNR sin mezclar tantas variaciones debidas al cambio de dirección.

### Peatón

El peatón representa un caso de receptor celular 5G con una ganancia de recepción menor que la de los vehículos. Su recorrido permite estudiar una situación más cercana a un usuario con un dispositivo móvil dentro del campus.

Tabla resumen sugerida:

| Receptor | Prx media (dBm) | SNR media (dB) | SNR mínima (dB) | Cobertura (%) |
|---|---:|---:|---:|---:|
| CampusVehicle | X | X | X | X |
| LinearVehicle | X | X | X | X |
| Pedestrian | X | X | X | X |

## 6. Análisis de cobertura según SNR

El análisis de cobertura se realiza utilizando la SNR como métrica principal. Para interpretar los resultados se emplean los umbrales definidos anteriormente: 20 dB, 13 dB y 0 dB. Estos límites permiten clasificar la cobertura como excelente, buena, aceptable o insuficiente.

Primero se analiza la configuración base con una potencia de transmisión de 30 dBm. En este caso se observan las zonas donde la SNR se mantiene por encima del umbral de cobertura y aquellas en las que el receptor queda por debajo del límite.

Después se repite la prueba aumentando la potencia de transmisión a 55.44 dBm, valor correspondiente a la potencia máxima indicada en la ficha técnica de la antena. Esta comparación permite observar cómo cambia la cobertura al utilizar una potencia de transmisión mayor.

Comparaciones sugeridas:

- Mapa de calor con 30 dBm
- Mapa de calor con 55.44 dBm
- SNR frente al tiempo con 30 dBm
- SNR frente al tiempo con 55.44 dBm
- Porcentaje de cobertura de cada receptor

Tabla sugerida:

| Receptor | Cobertura 30 dBm | Cobertura 55.44 dBm | Mejora |
|---|---:|---:|---:|
| CampusVehicle | X % | X % | X % |
| LinearVehicle | X % | X % | X % |
| Pedestrian | X % | X % | X % |

## 7. Comparativa entre configuraciones

Para comparar configuraciones, se mantiene fija la configuración base y se modifica únicamente el método de reconstrucción del patrón de radiación. De esta forma, se puede estudiar cómo afecta el patrón de antena a la cobertura sin introducir cambios adicionales en el modelo de propagación o en los receptores.

Las pruebas se realizan usando FSPL para evitar variaciones debidas al modelo de entorno o al shadowing. Esto permite comparar de forma más directa los métodos de reconstrucción.

Configuraciones sugeridas:

| Prueba | Modelo | Método patrón | Parámetro |
|---|---|---|---|
| A | FSPL | Omnidireccional | - |
| B | FSPL | Gil | - |
| C | FSPL | Vasiliadis | k = 1 |
| D | FSPL | Vasiliadis | k = 2 |

Aspectos a comparar:

- Forma del patrón reconstruido
- Mapa de calor generado
- Potencia recibida media por receptor
- SNR media por receptor
- Porcentaje de cobertura

Tabla sugerida:

| Método | CampusVehicle cobertura | LinearVehicle cobertura | Pedestrian cobertura |
|---|---:|---:|---:|
| Omni | X % | X % | X % |
| Gil | X % | X % | X % |
| Vasiliadis k = 1 | X % | X % | X % |
| Vasiliadis k = 2 | X % | X % | X % |

## 8. Limitaciones detectadas

En este apartado se recogen las principales limitaciones observadas durante las pruebas.

La primera limitación está relacionada con el modelado de los edificios. En la simulación se considera una pérdida fija por pared atravesada, tomando como referencia el hormigón. Sin embargo, en un escenario real no todos los edificios tienen los mismos materiales ni el mismo grosor. Además, los edificios del modelo están huecos, por lo que no se representa de forma detallada la propagación en interiores ni las pérdidas acumuladas dentro del edificio.

Otra limitación está relacionada con la detección de colisiones. El sistema calcula las pérdidas adicionales en función de los colliders atravesados por la línea entre transmisor y receptor. Aunque esto permite aproximar el efecto de los obstáculos, no reproduce todos los fenómenos reales de propagación, como difracción, reflexión, dispersión o multitrayecto.

También se detecta una limitación en la representación del mapa de calor. Al generar la rejilla tridimensional, algunos voxeles pueden atravesar el suelo o quedar parcialmente por debajo del terreno, especialmente cuando el terreno no es completamente plano. Esto no invalida el cálculo, pero puede afectar a la interpretación visual en ciertas zonas del escenario.

Además, las gráficas frente a distancia deben interpretarse con cuidado. En un escenario tridimensional, dos puntos situados a la misma distancia del transmisor pueden tener valores de potencia y SNR muy distintos debido a la orientación del patrón de radiación, la altura o los obstáculos atravesados. Por tanto, estas gráficas son útiles para comparar configuraciones bajo el mismo recorrido, pero no representan una relación única entre distancia y cobertura.

Por último, el simulador no modela interferencias de otros transmisores. Por este motivo, la métrica utilizada se basa en SNR, o en SINR con interferencias nulas, lo que simplifica el análisis pero no representa una red celular completa con múltiples celdas o fuentes interferentes.

## Orden recomendado de pruebas

1. Validar patrón con MATLAB
2. Validar FSPL con esferas debug y cálculo manual
3. Mostrar mapas de calor base
4. Analizar receptores móviles
5. Comparar 30 dBm frente a 55.44 dBm
6. Comparar métodos de reconstrucción usando FSPL
7. Cerrar con limitaciones
