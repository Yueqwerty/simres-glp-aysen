#!/usr/bin/env python3
"""
Orquestador avanzado de experimentos masivos para análisis de resiliencia.
Implementa paralelización inteligente, gestión de memoria y monitoreo en tiempo real.
"""
import json
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

import typer
from tqdm import tqdm

# Importar script de simulación individual
sys.path.append(str(Path(__file__).parent))

app = typer.Typer(
    name="ejecutar_experimentos",
    help="Orquestador avanzado de experimentos de simulación masiva",
    add_completion=False
)


def ejecutar_experimento_worker(config_path: Path, output_dir: Path) -> Dict[str, Any]:
    """Worker function para ejecutar un experimento individual."""
    try:
        # Importar aquí para evitar problemas de multiprocessing
        import subprocess
        import sys
        
        # Ejecutar simulación como subproceso
        cmd = [
            sys.executable, 
            "scripts/ejecutar_simulacion.py", 
            "ejecutar",
            str(config_path), 
            str(output_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
        
        if result.returncode == 0:
            return {"config": config_path.name, "status": "success", "output": result.stdout}
        else:
            return {"config": config_path.name, "status": "error", "error": result.stderr}
            
    except Exception as e:
        return {"config": config_path.name, "status": "error", "error": str(e)}


@app.command()
def ejecutar_paralelo(
    configs_dir: Path = typer.Argument(..., help="Directorio con archivos de configuración"),
    results_dir: Path = typer.Argument(..., help="Directorio de resultados"),
    max_workers: int = typer.Option(None, help="Máximo número de workers paralelos"),
    design: str = typer.Option("factorial", help="Tipo de diseño experimental")
) -> None:
    """Ejecuta experimentos en paralelo usando multiprocessing."""
    
    if max_workers is None:
        max_workers = min(32, mp.cpu_count())
    
    typer.echo(f"🚀 Iniciando experimentos paralelos con {max_workers} workers")
    
    # Crear directorio de resultados
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Obtener archivos de configuración
    config_files = list(configs_dir.glob("*.yaml")) + list(configs_dir.glob("*.yml"))
    typer.echo(f"📁 Encontrados {len(config_files)} archivos de configuración")
    
    if not config_files:
        typer.echo("❌ No se encontraron archivos de configuración", err=True)
        raise typer.Exit(1)
    
    # Ejecutar en paralelo con barra de progreso
    inicio_tiempo = time.time()
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Enviar trabajos
        futures = []
        for config_file in config_files:
            output_path = results_dir / config_file.stem
            future = executor.submit(ejecutar_experimento_worker, config_file, output_path)
            futures.append((future, config_file.name))
        
        # Procesar resultados con barra de progreso
        resultados = []
        with tqdm(total=len(futures), desc="Experimentos", unit="exp") as pbar:
            for future, config_name in futures:
                try:
                    resultado = future.result(timeout=600)  # 10 minutos timeout por experimento
                    resultados.append(resultado)
                    
                    # Actualizar barra de progreso
                    if resultado["status"] == "success":
                        pbar.set_postfix({"✅": config_name[:20]})
                    else:
                        pbar.set_postfix({"❌": config_name[:20]})
                    
                    pbar.update(1)
                    
                except Exception as e:
                    resultados.append({
                        "config": config_name,
                        "status": "timeout_error", 
                        "error": str(e)
                    })
                    pbar.set_postfix({"⏰": config_name[:20]})
                    pbar.update(1)
    
    # Calcular estadísticas finales
    tiempo_total = time.time() - inicio_tiempo
    exitosos = sum(1 for r in resultados if r["status"] == "success")
    errores = len(resultados) - exitosos
    
    typer.echo(f"\n🎉 Experimentos completados en {tiempo_total:.1f} segundos")
    typer.echo(f"✅ Experimentos exitosos: {exitosos}/{len(resultados)}")
    
    if errores > 0:
        typer.echo(f"❌ Experimentos con errores: {errores}")
        
        # Mostrar detalles de errores
        for resultado in resultados:
            if resultado["status"] != "success":
                typer.echo(f"   - {resultado['config']}: {resultado.get('error', 'Error desconocido')}")
    
    # Guardar reporte de ejecución
    reporte = {
        'timestamp': time.time(),
        'duracion_total_segundos': tiempo_total,
        'experimentos_totales': len(resultados),
        'experimentos_exitosos': exitosos,
        'experimentos_fallidos': errores,
        'configuracion': {
            'max_workers': max_workers,
            'design_type': design,
            'configs_directory': str(configs_dir),
            'results_directory': str(results_dir)
        },
        'resultados_detallados': resultados
    }
    
    reporte_path = results_dir / 'reporte_experimentos.json'
    with open(reporte_path, 'w') as f:
        json.dump(reporte, f, indent=2)
    
    typer.echo(f"📄 Reporte guardado en: {reporte_path}")


@app.command() 
def generar_factorial(
    base_config: Path = typer.Argument(..., help="Archivo de configuración base"),
    output_dir: Path = typer.Argument(..., help="Directorio para configuraciones generadas"),
    factores: str = typer.Option("numero_camiones:2,3,4;capacidad_planta:100000,150000", 
                                help="Factores en formato factor:val1,val2;factor2:val1,val2")
) -> None:
    """Genera diseño factorial de experimentos."""
    
    typer.echo("🧬 Generando diseño factorial de experimentos...")
    
    if not base_config.exists():
        typer.echo(f"❌ Configuración base no encontrada: {base_config}", err=True)
        raise typer.Exit(1)
    
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parsear factores
    factores_dict = {}
    try:
        for factor_spec in factores.split(';'):
            nombre, valores_str = factor_spec.split(':')
            valores = valores_str.split(',')
            # Convertir valores numéricos
            valores_procesados = []
            for val in valores:
                try:
                    # Intentar convertir a int primero, luego float
                    if '.' in val:
                        valores_procesados.append(float(val))
                    else:
                        valores_procesados.append(int(val))
                except ValueError:
                    valores_procesados.append(val.strip())  # Mantener como string
            
            factores_dict[nombre.strip()] = valores_procesados
    
    except Exception as e:
        typer.echo(f"❌ Error parseando factores: {e}", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"📊 Factores identificados: {factores_dict}")
    
    # Generar todas las combinaciones
    import itertools
    import yaml
    
    # Cargar configuración base
    with open(base_config, 'r') as f:
        config_base = yaml.safe_load(f)
    
    nombres_factores = list(factores_dict.keys())
    valores_factores = list(factores_dict.values())
    
    combinaciones = list(itertools.product(*valores_factores))
    typer.echo(f"🔢 Generando {len(combinaciones)} combinaciones factoriales")
    
    # Generar configuraciones
    for i, combinacion in enumerate(combinaciones):
        # Copiar configuración base
        config_experimento = config_base.copy()
        
        # Aplicar valores de factores
        for j, nombre_factor in enumerate(nombres_factores):
            valor_factor = combinacion[j]
            
            # Aplicar según el factor
            if nombre_factor == 'numero_camiones':
                # Ajustar número de camiones en entidades
                entidades_base = list(config_experimento.get('entidades', {}).keys())
                config_experimento['entidades'] = {}
                
                for k in range(valor_factor):
                    config_experimento['entidades'][f'camion_factorial_{k:02d}'] = {
                        'capacidad': 20000,
                        'base_operacional': 'Puerto Chacabuco',
                        'ruta_principal': f'Ruta_{k}'
                    }
            
            elif nombre_factor == 'capacidad_planta':
                if 'planta' not in config_experimento:
                    config_experimento['planta'] = {}
                config_experimento['planta']['capacidad_maxima'] = valor_factor
                
            elif nombre_factor == 'duracion':
                if 'simulacion' not in config_experimento:
                    config_experimento['simulacion'] = {}
                config_experimento['simulacion']['duracion'] = valor_factor
            
            # Añadir otros factores personalizados aquí
        
        # Añadir metadatos del experimento
        config_experimento['metadata_experimento'] = {
            'experimento_id': f'factorial_{i:04d}',
            'combinacion_factores': dict(zip(nombres_factores, combinacion)),
            'tipo_diseño': 'factorial_completo'
        }
        
        # Guardar configuración
        nombre_archivo = f'factorial_{i:04d}.yaml'
        archivo_salida = output_dir / nombre_archivo
        
        with open(archivo_salida, 'w') as f:
            yaml.dump(config_experimento, f, indent=2, default_flow_style=False)
    
    typer.echo(f"✅ Generadas {len(combinaciones)} configuraciones en {output_dir}")


@app.command()
def ejecutar_individual(
    config_path: Path = typer.Argument(..., help="Archivo de configuración"),
    output_path: Path = typer.Argument(..., help="Directorio de salida"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Modo verbose")
) -> None:
    """Ejecuta un experimento individual."""
    
    if verbose:
        typer.echo(f"🔧 Ejecutando experimento individual")
        typer.echo(f"   - Configuración: {config_path}")
        typer.echo(f"   - Salida: {output_path}")
    
    resultado = ejecutar_experimento_worker(config_path, output_path)
    
    if resultado["status"] == "success":
        typer.echo("✅ Experimento completado exitosamente")
        if verbose and "output" in resultado:
            typer.echo(f"Salida: {resultado['output']}")
    else:
        typer.echo(f"❌ Error en experimento: {resultado.get('error', 'Error desconocido')}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()