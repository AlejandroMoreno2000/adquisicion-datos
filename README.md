## Requisitos y estructura del repositorio

Este repositorio contiene todos los archivos y scripts necesarios para la toma, captura y almacenamiento de trazas electromagnéticas generadas durante la ejecución de software malicioso y benigno. Está diseñado específicamente para funcionar con el osciloscopio PicoScope 5000A Series. La implementación parte del proyecto de adquisición de datos desarrollado por el equipo de investigación de Duy-Phuc Pham et al. ([repositorio original](github.com/ahma-hub/data-acquisition)).
La versión incluida en este repositorio ha sido modificada y adaptada para ser plenamente compatible con los modelos PicoScope 5000A y para integrarse correctamente dentro del sistema desarrollado en el marco de este proyecto.

Requisitos previos

## Antes de ejecutar el sistema de captura, es necesario:
1. Instalar las dependencias de Python definidas en el archivo requirements.txt:
```
pip install -r requirements.txt
```
2. Contar con el ejecutable wrapper compilado y accesible en el sistema objetivo. (ver sección "Wrapper").


## Generación de trazas
El script principal de captura es generate_traces_pico.py. Se ejecuta con los siguientes parámetros:
```
generate_traces_pico.py [-c NUMERO] [-d DESTINO] [-n NBSAMPLES]
                        [--timebase TIMEBASE] [-t CANAL]
                        [-w WRAPPER_PATH] [-v] cmdFile
```

>  Descripción de los parámetros: 
cmdFile: ruta al archivo CSV que contiene los comandos a ejecutar.

* c: número de trazas a capturar por archivo.

* d: ruta de almacenamiento para las trazas capturadas.

* n: número de muestras por traza.

* -timebase: configuración del timebase del osciloscopio.

* t: canal del osciloscopio utilizado para la captura.

* w: ruta absoluta al ejecutable wrapper en el equipo objetivo.

* v: activa el modo de depuración (debug).


## Ejemplo de ejecución

Este es el comando utilizado durante los experimentos del Trabajo de Fin de Grado para capturar las trazas:
```
python3.10 ./generate_traces_pico.py ./cmdFiles/cmdFile_experimento.csv \
  -c 1250 -d /Volumes/Micron_5 -t A --timebase 254 -n 1000000 \
  -w /home/nics/Desktop/dataset/wrapper
```
Este comando ejecuta:

- 1.250 trazas por archivo,

- 1.000.000 de muestras por traza,

- usando el canal A con timebase = 254.

Los comandos que se ejecutan se extraen del archivo cmdFile_experimento.csv.

## Formato del archivo de comandos (cmdFile)

El archivo CSV debe tener una línea por cada conjunto de comandos, con el siguiente formato:
```
comando-pretrigger,comando-principal,tag
```
En cada iteración, el sistema realiza las siguientes acciones:

  - Ejecución del comando pretrigger previo al comando principal (por ejemplo, un descifrador en el caso de haber ejecutado un ransomware previamente).

  - Armado el osciloscopio.

  - Ejecución del comando principal, que genera la traza.

  - Almacenamiento de la señal en formato binario con la estructura tag-randomId.dat.

> Ejemplo de línea en cmdFile:
```
/home/nics/Desktop/dataset/malware/original/gonnacry/decryptor, /home/nics/Desktop/dataset/malware/original/gonnacry/gonnacry_Camellia_256_CBC, gonnacry-Camellia-256-CBC
```

## Wrapper

El wrapper es un ejecutable ligero, desarrollado en C, que reside en el sistema objetivo y cuya función es coordinar la ejecución de comandos durante la ventana de captura configurada por el sistema de adquisición. Este componente es activado automáticamente desde el script generate_traces_pico.py.

El proyecto original de Duy-Phuc Pham et al. incluía un wrapper diseñado para ejecutarse en entornos Linux embebidos, como Raspberry Pi. Sin embargo, dado que en este proyecto el sistema objetivo es un ordenador con Windows, dicho wrapper no resultaba compatible.

Por este motivo, se desarrolló una nueva implementación del wrapper adaptada a este entorno. Este nuevo programa replica la funcionalidad esperada: ejecuta un comando recibido por línea de comandos y, si se indica una duración en microsegundos, lo lanza en un hilo independiente y lo finaliza tras ese intervalo. En caso contrario, espera a que el comando termine por sí solo. Todo ello se implementa utilizando llamadas a system() y funciones de temporización basadas en pthread y nanosleep.

Este ejecutable debe:
- Estar disponible en la ruta indicada mediante el parámetro -w al invocar generate_traces_pico.py.

- Tener permisos de ejecución adecuados en el sistema objetivo.

Gracias a este componente, se logra la sincronización precisa entre el inicio de la ejecución de los comandos maliciosos o benignos y la adquisición de las señales por parte del osciloscopio.
