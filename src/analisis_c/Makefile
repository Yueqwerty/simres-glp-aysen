# Makefile para compilar kernel de análisis de secuencias
CC = gcc
CFLAGS = -Wall -Wextra -O3 -fPIC
LDFLAGS = -shared

# Detectar plataforma automáticamente
UNAME_S := $(shell uname -s)

# Configuración específica por plataforma
ifeq ($(UNAME_S),Linux)
    TARGET = sequence_analyzer.so
    CFLAGS += -std=c99
endif

ifeq ($(UNAME_S),Darwin)
    TARGET = sequence_analyzer.dylib
    LDFLAGS += -undefined dynamic_lookup
    CFLAGS += -std=c99
endif

ifeq ($(OS),Windows_NT)
    TARGET = sequence_analyzer.dll
    CC = gcc
endif

# Archivos fuente
SOURCE = sequence_analyzer.c
OBJECTS = sequence_analyzer.o

# Regla principal
all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(LDFLAGS) -o $(TARGET) $(OBJECTS)
	@echo "✅ Kernel compilado exitosamente: $(TARGET)"

$(OBJECTS): $(SOURCE)
	$(CC) $(CFLAGS) -c $(SOURCE)

# Limpieza
clean:
	rm -f $(OBJECTS) $(TARGET) *.so *.dylib *.dll
	@echo "🧹 Archivos de compilación limpiados"

# Instalación (copia a directorio padre para fácil acceso)
install: $(TARGET)
	cp $(TARGET) ../$(TARGET)
	@echo "📦 Kernel instalado en directorio padre"

# Test básico
test: $(TARGET)
	@echo "🧪 Ejecutando test básico..."
	@python3 -c "import ctypes; lib = ctypes.CDLL('./$(TARGET)'); print('Kernel cargado correctamente')" || echo "❌ Error cargando kernel"

# Información del sistema
info:
	@echo "🔍 Información del sistema:"
	@echo "   Sistema: $(UNAME_S)"
	@echo "   Compilador: $(CC)"
	@echo "   Flags: $(CFLAGS)"
	@echo "   Target: $(TARGET)"

# Compilación con debug
debug: CFLAGS += -g -DDEBUG
debug: $(TARGET)

# Ayuda
help:
	@echo "🛠️  Makefile para kernel de análisis de secuencias"
	@echo ""
	@echo "Targets disponibles:"
	@echo "  all      - Compilar kernel (default)"
	@echo "  clean    - Limpiar archivos de compilación"
	@echo "  install  - Instalar kernel en directorio padre"
	@echo "  test     - Ejecutar test básico"
	@echo "  debug    - Compilar con símbolos de debug"
	@echo "  info     - Mostrar información del sistema"
	@echo "  help     - Mostrar esta ayuda"

.PHONY: all clean install test info debug help