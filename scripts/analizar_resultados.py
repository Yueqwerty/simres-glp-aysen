#!/usr/bin/env python3
"""
Script avanzado de análisis de resultados con algoritmos de ML y grafos.
Implementa clustering de arquetipos de fallo y análisis de secuencias críticas.
"""

import ctypes
import json
import logging
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from scipy import stats
from scipy.stats import f_oneway, kruskal, levene, bartlett
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import itertools
import networkx as nx
import numpy as np
import pandas as pd
import typer
from sklearn.cluster import DBSCAN, KMeans
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de warnings y logging
warnings.filterwarnings('ignore', category=FutureWarning)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="analizar_resultados",
    help="Análisis avanzado de resultados de simulación con ML y teoría de grafos",
    add_completion=False
)

# ============================================================================
# CLASES DE SOPORTE PARA ANÁLISIS AVANZADO
# ============================================================================

class KernelCLoader:
    """
    Cargador inteligente del kernel en C con detección automática de plataforma.
    Implementa patrones Singleton y Factory para gestión de recursos.
    """
    
    _instance: Optional['KernelCLoader'] = None
    _library: Optional[ctypes.CDLL] = None
    
    def __new__(cls) -> 'KernelCLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._library is None:
            self._load_library()
    
    def _load_library(self) -> None:
        """Carga la librería compartida con detección automática de plataforma."""
        kernel_dir = Path(__file__).parent / "src" / "analisis_c"
        
        # Detectar extensión según plataforma
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            lib_name = "sequence_analyzer.dll"
        elif system == "darwin":
            lib_name = "sequence_analyzer.dylib"
        else:
            lib_name = "sequence_analyzer.so"
        
        lib_path = kernel_dir / lib_name
        
        if not lib_path.exists():
            logger.warning(f"Kernel en C no encontrado: {lib_path}. Usando fallback Python.")
            self._library = None
            return
        
        try:
            self._library = ctypes.CDLL(str(lib_path))
            self._configure_function_signatures()
            logger.info(f"Kernel en C cargado exitosamente: {lib_path}")
        except Exception as e:
            logger.warning(f"Error cargando kernel en C: {e}. Usando fallback Python.")
            self._library = None
    
    def _configure_function_signatures(self) -> None:
        """Configura las signaturas de funciones para interoperabilidad segura."""
        if not self._library:
            return
        
        # Configurar build_transition_graph
        self._library.build_transition_graph.argtypes = [
            ctypes.POINTER(ctypes.c_int),  # sequence
            ctypes.c_int,                   # length
            ctypes.POINTER(ctypes.c_int)    # result_size
        ]
        self._library.build_transition_graph.restype = ctypes.c_void_p
        
        # Configurar get_adjacency_matrix
        self._library.get_adjacency_matrix.argtypes = [
            ctypes.c_void_p,                # graph
            ctypes.POINTER(ctypes.c_int)    # matrix_size
        ]
        self._library.get_adjacency_matrix.restype = ctypes.POINTER(ctypes.c_int)
        
        # Configurar detect_cycles
        self._library.detect_cycles.argtypes = [ctypes.c_void_p]
        self._library.detect_cycles.restype = ctypes.c_bool
        
        # Configurar free_transition_graph
        self._library.free_transition_graph.argtypes = [ctypes.c_void_p]
        self._library.free_transition_graph.restype = None
    
    @property
    def library(self) -> Optional[ctypes.CDLL]:
        """Acceso thread-safe a la librería cargada."""
        return self._library


class AnalizadorSecuencias:
    """
    Analizador avanzado de secuencias usando el kernel en C y NetworkX.
    Implementa algoritmos de grafos y análisis de patrones críticos.
    """
    
    def __init__(self):
        self.kernel = KernelCLoader()
        self.graph_cache: Dict[str, nx.DiGraph] = {}
    
    def construir_grafo_transicion(self, secuencia_eventos: List[int]) -> nx.DiGraph:
        """
        Construye un grafo de transición usando el kernel optimizado en C o fallback Python.
        """
        if len(secuencia_eventos) <= 1:
            return nx.DiGraph()
        
        # Intentar usar kernel en C primero
        if self.kernel.library:
            return self._construir_grafo_c(secuencia_eventos)
        else:
            return self._construir_grafo_python(secuencia_eventos)
    
    def _construir_grafo_c(self, secuencia_eventos: List[int]) -> nx.DiGraph:
        """Construcción usando kernel en C."""
        try:
            sequence_array = (ctypes.c_int * len(secuencia_eventos))(*secuencia_eventos)
            result_size = ctypes.c_int()
            
            graph_ptr = self.kernel.library.build_transition_graph(
                sequence_array, 
                len(secuencia_eventos), 
                ctypes.byref(result_size)
            )
            
            if not graph_ptr:
                return self._construir_grafo_python(secuencia_eventos)
            
            try:
                matrix_size = ctypes.c_int()
                matrix_ptr = self.kernel.library.get_adjacency_matrix(
                    graph_ptr, 
                    ctypes.byref(matrix_size)
                )
                
                if not matrix_ptr or matrix_size.value == 0:
                    return nx.DiGraph()
                
                n = matrix_size.value
                matrix_data = np.ctypeslib.as_array(matrix_ptr, shape=(n * n,))
                adjacency_matrix = matrix_data.reshape((n, n)).copy()
                
                G = nx.from_numpy_array(
                    adjacency_matrix, 
                    create_using=nx.DiGraph,
                    parallel_edges=False
                )
                
                tiene_ciclos = self.kernel.library.detect_cycles(graph_ptr)
                G.graph['has_cycles'] = bool(tiene_ciclos)
                G.graph['num_nodes'] = n
                G.graph['num_edges'] = result_size.value
                
                return G
                
            finally:
                self.kernel.library.free_transition_graph(graph_ptr)
        
        except Exception as e:
            logger.warning(f"Error en kernel C: {e}. Usando fallback Python.")
            return self._construir_grafo_python(secuencia_eventos)
    
    def _construir_grafo_python(self, secuencia_eventos: List[int]) -> nx.DiGraph:
        """Implementación fallback en Python puro."""
        G = nx.DiGraph()
        
        # Contar transiciones
        transiciones = Counter()
        for i in range(len(secuencia_eventos) - 1):
            from_node = secuencia_eventos[i]
            to_node = secuencia_eventos[i + 1]
            transiciones[(from_node, to_node)] += 1
        
        # Agregar nodos y aristas
        for (from_node, to_node), weight in transiciones.items():
            G.add_edge(from_node, to_node, weight=weight)
        
        # Detectar ciclos
        try:
            has_cycles = not nx.is_directed_acyclic_graph(G)
        except:
            has_cycles = False
        
        G.graph['has_cycles'] = has_cycles
        G.graph['num_nodes'] = G.number_of_nodes()
        G.graph['num_edges'] = G.number_of_edges()
        
        return G
    
    def analizar_centralidad(self, grafo: nx.DiGraph) -> Dict[str, Any]:
        """
        Calcula métricas de centralidad para identificar nodos críticos.
        """
        if grafo.number_of_nodes() == 0:
            return {}
        
        try:
            # Centralidad de grado (in/out)
            in_centrality = nx.in_degree_centrality(grafo)
            out_centrality = nx.out_degree_centrality(grafo)
            
            # Centralidad de intermediación (betweenness)
            betweenness = nx.betweenness_centrality(grafo, normalized=True)
            
            # Centralidad de cercanía (closeness)
            try:
                closeness = nx.closeness_centrality(grafo)
            except:
                closeness = {}
            
            # PageRank (autoridad en grafos dirigidos)
            try:
                pagerank = nx.pagerank(grafo, alpha=0.85, max_iter=1000)
            except:
                pagerank = {}
            
            # Identificar nodos más críticos
            nodos_criticos = []
            for nodo in grafo.nodes():
                criticidad = (
                    betweenness.get(nodo, 0) * 0.4 +
                    pagerank.get(nodo, 0) * 0.3 +
                    in_centrality.get(nodo, 0) * 0.2 +
                    out_centrality.get(nodo, 0) * 0.1
                )
                nodos_criticos.append((nodo, criticidad))
            
            nodos_criticos.sort(key=lambda x: x[1], reverse=True)
            
            return {
                'in_degree_centrality': in_centrality,
                'out_degree_centrality': out_centrality,
                'betweenness_centrality': betweenness,
                'closeness_centrality': closeness,
                'pagerank': pagerank,
                'nodos_criticos': nodos_criticos[:10],
                'has_cycles': grafo.graph.get('has_cycles', False)
            }
            
        except Exception as e:
            logger.error(f"Error calculando centralidad: {e}")
            return {}
    
    def encontrar_caminos_criticos(self, grafo: nx.DiGraph, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Identifica los caminos más críticos en el grafo de transición.
        """
        if grafo.number_of_nodes() < 2:
            return []
        
        caminos_criticos = []
        
        try:
            # Seleccionar nodos importantes basados en grado
            nodos = list(grafo.nodes())
            grados = dict(grafo.degree())
            nodos_importantes = sorted(nodos, key=lambda x: grados[x], reverse=True)[:min(10, len(nodos))]
            
            # Generar pares de nodos importantes
            pares_importantes = []
            for i, origen in enumerate(nodos_importantes[:5]):
                for destino in nodos_importantes[i+1:i+3]:
                    if origen != destino:
                        pares_importantes.append((origen, destino))
            
            # Calcular caminos más cortos ponderados
            for origen, destino in pares_importantes[:top_k]:
                try:
                    if nx.has_path(grafo, origen, destino):
                        camino = nx.shortest_path(
                            grafo, 
                            source=origen, 
                            target=destino, 
                            weight='weight'
                        )
                        
                        # Calcular peso total del camino
                        peso_total = 0
                        for i in range(len(camino) - 1):
                            u, v = camino[i], camino[i + 1]
                            peso_total += grafo[u][v].get('weight', 1)
                        
                        caminos_criticos.append({
                            'origen': origen,
                            'destino': destino,
                            'camino': camino,
                            'longitud': len(camino),
                            'peso_total': peso_total,
                            'peso_promedio': peso_total / max(len(camino) - 1, 1)
                        })
                        
                except nx.NetworkXNoPath:
                    continue
                except Exception as e:
                    logger.warning(f"Error calculando camino {origen}->{destino}: {e}")
                    continue
            
            caminos_criticos.sort(key=lambda x: x['peso_total'], reverse=True)
            return caminos_criticos[:top_k]
            
        except Exception as e:
            logger.error(f"Error encontrando caminos críticos: {e}")
            return []


class ClusterizadorFallos:
    """
    Sistema avanzado de clustering para identificar arquetipos de fallo.
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.vectorizer: Optional[Union[CountVectorizer, TfidfVectorizer]] = None
        self.scaler: Optional[StandardScaler] = None
        self.clustering_model: Optional[Union[DBSCAN, KMeans]] = None
        self.feature_matrix: Optional[np.ndarray] = None
    
    def preparar_datos_secuencias(self, 
                                 secuencias_fallo: List[List[str]], 
                                 metodo_vectorizacion: str = 'tfidf') -> np.ndarray:
        """
        Prepara y vectoriza secuencias de eventos de fallo para clustering.
        """
        if not secuencias_fallo:
            raise ValueError("Lista de secuencias vacía")
        
        # Convertir secuencias a strings para vectorización
        documentos = []
        for secuencia in secuencias_fallo:
            documento = ' '.join(secuencia)
            documentos.append(documento)
        
        # Configurar vectorizador según método
        if metodo_vectorizacion == 'tfidf':
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.95,
                stop_words=None,
                token_pattern=r'\b\w+\b'
            )
        elif metodo_vectorizacion == 'count':
            self.vectorizer = CountVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                binary=False,
                token_pattern=r'\b\w+\b'
            )
        else:  # binary
            self.vectorizer = CountVectorizer(
                max_features=500,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95,
                binary=True,
                token_pattern=r'\b\w+\b'
            )
        
        try:
            X = self.vectorizer.fit_transform(documentos)
            self.feature_matrix = X.toarray()
            
            if metodo_vectorizacion == 'count':
                self.scaler = StandardScaler(with_mean=False)
                self.feature_matrix = self.scaler.fit_transform(self.feature_matrix)
            
            logger.info(f"Vectorización completada: {self.feature_matrix.shape}")
            return self.feature_matrix
            
        except Exception as e:
            logger.error(f"Error en vectorización: {e}")
            raise
    
    def clustering_dbscan(self, eps: float = 0.5, min_samples: int = 3) -> Dict[str, Any]:
        """Aplica clustering DBSCAN para detectar arquetipos de fallo."""
        if self.feature_matrix is None:
            raise ValueError("Debe llamar preparar_datos_secuencias primero")
        
        self.clustering_model = DBSCAN(
            eps=eps,
            min_samples=min_samples,
            metric='cosine',
            n_jobs=-1
        )
        
        try:
            labels = self.clustering_model.fit_predict(self.feature_matrix)
            
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)
            
            silhouette = None
            if n_clusters > 1 and n_noise < len(labels) - 1:
                mask = labels != -1
                if mask.sum() > 1:
                    try:
                        silhouette = silhouette_score(
                            self.feature_matrix[mask], 
                            labels[mask], 
                            metric='cosine'
                        )
                    except:
                        silhouette = None
            
            cluster_info = self._analizar_clusters(labels)
            
            return {
                'algoritmo': 'DBSCAN',
                'n_clusters': n_clusters,
                'n_noise_points': n_noise,
                'silhouette_score': silhouette,
                'labels': labels,
                'cluster_info': cluster_info,
                'parametros': {'eps': eps, 'min_samples': min_samples}
            }
            
        except Exception as e:
            logger.error(f"Error en clustering DBSCAN: {e}")
            raise
    
    def clustering_kmeans(self, n_clusters: int = None) -> Dict[str, Any]:
        """Aplica clustering K-means con selección automática de k."""
        if self.feature_matrix is None:
            raise ValueError("Debe llamar preparar_datos_secuencias primero")
        
        n_samples = self.feature_matrix.shape[0]
        
        if n_clusters is None:
            n_clusters = self._seleccionar_k_optimo()
        
        n_clusters = min(n_clusters, n_samples - 1)
        
        if n_clusters < 2:
            logger.warning("Muy pocas muestras para clustering significativo")
            n_clusters = 2
        
        self.clustering_model = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=10,
            max_iter=300
        )
        
        try:
            labels = self.clustering_model.fit_predict(self.feature_matrix)
            
            silhouette = silhouette_score(self.feature_matrix, labels, metric='cosine')
            inertia = self.clustering_model.inertia_
            
            cluster_info = self._analizar_clusters(labels)
            
            return {
                'algoritmo': 'K-means',
                'n_clusters': n_clusters,
                'silhouette_score': silhouette,
                'inertia': inertia,
                'labels': labels,
                'cluster_info': cluster_info,
                'centroids': self.clustering_model.cluster_centers_.tolist(),
                'parametros': {'n_clusters': n_clusters}
            }
            
        except Exception as e:
            logger.error(f"Error en clustering K-means: {e}")
            raise
    
    def _seleccionar_k_optimo(self, k_max: int = None) -> int:
        """Selecciona k óptimo usando método del codo y silhouette score."""
        n_samples = self.feature_matrix.shape[0]
        
        if k_max is None:
            k_max = min(10, n_samples // 2)
        
        k_range = range(2, min(k_max + 1, n_samples))
        
        if len(k_range) == 0:
            return 2
        
        silhouette_scores = []
        
        for k in k_range:
            try:
                kmeans = KMeans(
                    n_clusters=k, 
                    random_state=self.random_state,
                    n_init=5
                )
                labels = kmeans.fit_predict(self.feature_matrix)
                
                silhouette = silhouette_score(self.feature_matrix, labels, metric='cosine')
                silhouette_scores.append(silhouette)
                
            except Exception as e:
                logger.warning(f"Error evaluando k={k}: {e}")
                silhouette_scores.append(0)
        
        if not silhouette_scores:
            return 2
        
        best_k_idx = np.argmax(silhouette_scores)
        best_k = list(k_range)[best_k_idx]
        
        logger.info(f"K óptimo seleccionado: {best_k} (silhouette: {silhouette_scores[best_k_idx]:.3f})")
        
        return best_k
    
    def _analizar_clusters(self, labels: np.ndarray) -> Dict[str, Any]:
        """Analiza los clusters encontrados extrayendo características."""
        if self.vectorizer is None:
            return {}
        
        unique_labels = set(labels)
        cluster_analysis = {}
        
        try:
            feature_names = self.vectorizer.get_feature_names_out()
        except AttributeError:
            feature_names = self.vectorizer.get_feature_names()
        
        for label in unique_labels:
            if label == -1:
                cluster_name = 'noise'
            else:
                cluster_name = f'cluster_{label}'
            
            mask = labels == label
            cluster_size = mask.sum()
            
            if cluster_size == 0:
                continue
            
            cluster_features = self.feature_matrix[mask]
            centroid = np.mean(cluster_features, axis=0)
            
            top_indices = np.argsort(centroid)[-10:][::-1]
            top_features = [(feature_names[i], centroid[i]) for i in top_indices if centroid[i] > 0]
            
            cluster_analysis[cluster_name] = {
                'size': int(cluster_size),
                'percentage': float(cluster_size / len(labels) * 100),
                'top_features': top_features,
                'centroid_norm': float(np.linalg.norm(centroid))
            }
        
        return cluster_analysis
    
    def generar_embedding_2d(self, metodo: str = 'tsne') -> np.ndarray:
        """Genera embedding 2D para visualización usando t-SNE."""
        if self.feature_matrix is None:
            raise ValueError("Debe llamar preparar_datos_secuencias primero")
        
        if metodo.lower() == 'tsne':
            if self.feature_matrix.shape[1] > 50:
                pca = PCA(n_components=50, random_state=self.random_state)
                features_reduced = pca.fit_transform(self.feature_matrix)
            else:
                features_reduced = self.feature_matrix
            
            perplexity = min(30, features_reduced.shape[0] - 1, 5)
            if perplexity < 5:
                perplexity = 5
            
            tsne = TSNE(
                n_components=2,
                random_state=self.random_state,
                perplexity=perplexity,
                n_iter=1000,
                init='pca'
            )
            
            embedding = tsne.fit_transform(features_reduced)
            return embedding
        
        else:
            raise ValueError(f"Método de embedding no soportado: {metodo}")


class AnalizadorANOVA:
    """
    Analizador especializado para ANOVA factorial y análisis de varianza avanzado.
    """
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha
        self.resultados_anova: Dict[str, Any] = {}
        
    def analisis_factorial_completo(self, 
                                  df_resultados: pd.DataFrame, 
                                  factores: List[str], 
                                  variables_respuesta: List[str]) -> Dict[str, Any]:
        """
        Realiza análisis ANOVA factorial completo.
        """
        
        resultados = {
            'configuracion': {
                'alpha': self.alpha,
                'num_factores': len(factores),
                'num_variables_respuesta': len(variables_respuesta),
                'tamaño_muestra': len(df_resultados)
            },
            'analisis_por_variable': {},
            'resumen_significancia': {},
            'recomendaciones': []
        }
        
        for variable in variables_respuesta:
            if variable not in df_resultados.columns:
                logger.warning(f"Variable {variable} no encontrada en los datos")
                continue
                
            try:
                resultado_var = self._analisis_anova_variable(
                    df_resultados, factores, variable
                )
                resultados['analisis_por_variable'][variable] = resultado_var
                
            except Exception as e:
                logger.error(f"Error analizando variable {variable}: {e}")
                continue
        
        resultados['resumen_significancia'] = self._resumen_significancia(
            resultados['analisis_por_variable']
        )
        
        resultados['recomendaciones'] = self._generar_recomendaciones(
            resultados['resumen_significancia']
        )
        
        return resultados
    
    def _analisis_anova_variable(self, 
                                df: pd.DataFrame, 
                                factores: List[str], 
                                variable: str) -> Dict[str, Any]:
        """Realiza análisis ANOVA completo para una variable específica."""
        
        # Verificar supuestos estadísticos
        normalidad = self._test_normalidad(df[variable])
        homoscedasticidad = self._test_homoscedasticidad(df, factores, variable)
        
        resultado = {
            'variable_respuesta': variable,
            'supuestos': {
                'normalidad': normalidad,
                'homoscedasticidad': homoscedasticidad
            },
            'efectos_principales': {},
            'interacciones': {},
            'post_hoc': {},
            'tamaño_efecto': {}
        }
        
        # Análisis de efectos principales
        for factor in factores:
            if factor in df.columns:
                efecto = self._analisis_efecto_principal(df, factor, variable)
                resultado['efectos_principales'][factor] = efecto
        
        # ANOVA factorial usando statsmodels
        resultado['anova_factorial'] = self._anova_factorial_statsmodels(
            df, factores, variable
        )
        
        return resultado
    
    def _test_normalidad(self, serie: pd.Series) -> Dict[str, Any]:
        """Pruebas de normalidad múltiples."""
        serie_clean = serie.dropna()
        
        if len(serie_clean) < 3:
            return {'error': 'Muy pocas observaciones para test de normalidad'}
        
        resultados = {}
        
        # Shapiro-Wilk
        if len(serie_clean) <= 5000:
            try:
                stat, p_value = stats.shapiro(serie_clean)
                resultados['shapiro_wilk'] = {
                    'statistic': float(stat),
                    'p_value': float(p_value),
                    'normal': p_value > self.alpha
                }
            except:
                resultados['shapiro_wilk'] = {'error': 'Error en test Shapiro-Wilk'}
        
        # Kolmogorov-Smirnov
        try:
            stat, p_value = stats.kstest(serie_clean, 'norm', 
                                       args=(serie_clean.mean(), serie_clean.std()))
            resultados['kolmogorov_smirnov'] = {
                'statistic': float(stat),
                'p_value': float(p_value),
                'normal': p_value > self.alpha
            }
        except:
            resultados['kolmogorov_smirnov'] = {'error': 'Error en test K-S'}
        
        # Conclusión general
        tests_normales = 0
        if 'shapiro_wilk' in resultados and resultados['shapiro_wilk'].get('normal', False):
            tests_normales += 1
        if 'kolmogorov_smirnov' in resultados and resultados['kolmogorov_smirnov'].get('normal', False):
            tests_normales += 1
        
        resultados['conclusion'] = {
            'es_normal': tests_normales >= 1,
            'nivel_confianza': tests_normales / 2.0
        }
        
        return resultados
    
    def _test_homoscedasticidad(self, 
                               df: pd.DataFrame, 
                               factores: List[str], 
                               variable: str) -> Dict[str, Any]:
        """Pruebas de homoscedasticidad."""
        
        resultados = {}
        
        for factor in factores:
            if factor not in df.columns:
                continue
                
            try:
                grupos = [group[variable].dropna() for name, group in df.groupby(factor)]
                grupos = [g for g in grupos if len(g) >= 2]
                
                if len(grupos) < 2:
                    continue
                
                # Test de Levene
                try:
                    stat, p_value = levene(*grupos, center='median')
                    levene_result = {
                        'statistic': float(stat),
                        'p_value': float(p_value),
                        'homoscedastico': p_value > self.alpha
                    }
                except:
                    levene_result = {'error': 'Error en test de Levene'}
                
                # Test de Bartlett
                try:
                    stat, p_value = bartlett(*grupos)
                    bartlett_result = {
                        'statistic': float(stat),
                        'p_value': float(p_value), 
                        'homoscedastico': p_value > self.alpha
                    }
                except:
                    bartlett_result = {'error': 'Error en test de Bartlett'}
                
                resultados[factor] = {
                    'levene': levene_result,
                    'bartlett': bartlett_result,
                    'conclusion': levene_result.get('homoscedastico', False)
                }
                
            except Exception as e:
                logger.warning(f"Error en test de homoscedasticidad para {factor}: {e}")
                continue
        
        return resultados
    
    def _analisis_efecto_principal(self, 
                                  df: pd.DataFrame, 
                                  factor: str, 
                                  variable: str) -> Dict[str, Any]:
        """Análisis de efecto principal de un factor."""
        
        grupos = []
        nombres_grupos = []
        for name, group in df.groupby(factor):
            valores = group[variable].dropna()
            if len(valores) > 0:
                grupos.append(valores)
                nombres_grupos.append(str(name))
        
        if len(grupos) < 2:
            return {'error': 'Insuficientes grupos para análisis'}
        
        resultado = {
            'factor': factor,
            'num_grupos': len(grupos),
            'tamaños_grupos': [len(g) for g in grupos],
            'nombres_grupos': nombres_grupos
        }
        
        # ANOVA de una vía
        try:
            f_stat, p_value = f_oneway(*grupos)
            resultado['anova_oneway'] = {
                'f_statistic': float(f_stat),
                'p_value': float(p_value),
                'significativo': p_value < self.alpha
            }
        except:
            resultado['anova_oneway'] = {'error': 'Error en ANOVA one-way'}
        
        # Test no paramétrico
        try:
            h_stat, p_value_kw = kruskal(*grupos)
            resultado['kruskal_wallis'] = {
                'h_statistic': float(h_stat),
                'p_value': float(p_value_kw),
                'significativo': p_value_kw < self.alpha
            }
        except:
            resultado['kruskal_wallis'] = {'error': 'Error en Kruskal-Wallis'}
        
        # Estadísticas descriptivas por grupo
        stats_por_grupo = []
        for i, grupo in enumerate(grupos):
            stats_por_grupo.append({
                'grupo': nombres_grupos[i],
                'n': len(grupo),
                'media': float(grupo.mean()),
                'std': float(grupo.std()),
                'mediana': float(grupo.median()),
                'min': float(grupo.min()),
                'max': float(grupo.max())
            })
        
        resultado['estadisticas_grupos'] = stats_por_grupo
        
        return resultado
    
    def _anova_factorial_statsmodels(self, 
                                    df: pd.DataFrame, 
                                    factores: List[str], 
                                    variable: str) -> Dict[str, Any]:
        """ANOVA factorial usando statsmodels."""
        
        columnas_necesarias = factores + [variable]
        df_clean = df[columnas_necesarias].dropna()
        
        if len(df_clean) < len(factores) * 4:
            return {'error': 'Datos insuficientes para ANOVA factorial'}
        
        try:
            # Construir fórmula factorial
            terminos_principales = [f"C({factor})" for factor in factores]
            
            interacciones_2vias = []
            for i in range(len(factores)):
                for j in range(i+1, len(factores)):
                    interacciones_2vias.append(f"C({factores[i]}):C({factores[j]})")
            
            todos_terminos = terminos_principales + interacciones_2vias[:3]  # Limitar interacciones
            formula = f"{variable} ~ " + " + ".join(todos_terminos)
            
            # Ajustar modelo
            modelo = ols(formula, data=df_clean).fit()
            tabla_anova = anova_lm(modelo, typ=2)
            
            resultado = {
                'formula': formula,
                'n_observaciones': len(df_clean),
                'r_squared': float(modelo.rsquared),
                'r_squared_adj': float(modelo.rsquared_adj),
                'efectos_detallados': {},
                'resumen_significancia': {}
            }
            
            efectos_principales = []
            interacciones_sig = []
            
            for index, row in tabla_anova.iterrows():
                efecto_nombre = str(index)
                p_value = float(row['PR(>F)']) if pd.notna(row['PR(>F)']) else 1.0
                significativo = p_value < self.alpha
                
                efecto_info = {
                    'sum_sq': float(row['sum_sq']),
                    'df': int(row['df']),
                    'mean_sq': float(row['sum_sq'] / row['df']) if row['df'] > 0 else 0,
                    'F': float(row['F']) if pd.notna(row['F']) else None,
                    'p_value': p_value,
                    'significativo': significativo
                }
                
                resultado['efectos_detallados'][efecto_nombre] = efecto_info
                
                if ':' not in efecto_nombre and 'Residual' not in efecto_nombre:
                    if significativo:
                        efectos_principales.append(efecto_nombre)
                elif ':' in efecto_nombre and significativo:
                    interacciones_sig.append(efecto_nombre)
            
            resultado['resumen_significancia'] = {
                'efectos_principales_significativos': efectos_principales,
                'interacciones_significativas': interacciones_sig,
                'total_efectos_significativos': len(efectos_principales) + len(interacciones_sig)
            }
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en ANOVA factorial: {e}")
            return {'error': str(e)}
    
    def _resumen_significancia(self, analisis_por_variable: Dict[str, Any]) -> Dict[str, Any]:
        """Genera resumen de significancia across all variables."""
        
        resumen = {
            'factores_mas_influyentes': {},
            'interacciones_importantes': {},
            'variables_mas_sensibles': {},
            'patron_significancia': {}
        }
        
        conteo_factores = {}
        conteo_interacciones = {}
        
        for variable, analisis in analisis_por_variable.items():
            # Efectos principales
            for factor, efecto in analisis.get('efectos_principales', {}).items():
                if efecto.get('anova_oneway', {}).get('significativo', False):
                    conteo_factores[factor] = conteo_factores.get(factor, 0) + 1
            
            # Interacciones del ANOVA factorial
            anova_factorial = analisis.get('anova_factorial', {})
            if 'resumen_significancia' in anova_factorial:
                for interaccion in anova_factorial['resumen_significancia'].get('interacciones_significativas', []):
                    conteo_interacciones[interaccion] = conteo_interacciones.get(interaccion, 0) + 1
        
        resumen['factores_mas_influyentes'] = dict(
            sorted(conteo_factores.items(), key=lambda x: x[1], reverse=True)
        )
        
        resumen['interacciones_importantes'] = dict(
            sorted(conteo_interacciones.items(), key=lambda x: x[1], reverse=True)
        )
        
        # Variables más sensibles
        sensibilidad_variables = {}
        for variable, analisis in analisis_por_variable.items():
            efectos_sig = 0
            
            for efecto in analisis.get('efectos_principales', {}).values():
                if efecto.get('anova_oneway', {}).get('significativo', False):
                    efectos_sig += 1
            
            anova_factorial = analisis.get('anova_factorial', {})
            if 'resumen_significancia' in anova_factorial:
                efectos_sig += anova_factorial['resumen_significancia'].get('total_efectos_significativos', 0)
            
            sensibilidad_variables[variable] = efectos_sig
        
        resumen['variables_mas_sensibles'] = dict(
            sorted(sensibilidad_variables.items(), key=lambda x: x[1], reverse=True)
        )
        
        return resumen
    
    def _generar_recomendaciones(self, resumen_significancia: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones basadas en el análisis ANOVA."""
        
        recomendaciones = []
        
        factores_top = list(resumen_significancia.get('factores_mas_influyentes', {}).keys())[:3]
        if factores_top:
            recomendaciones.append(
                f"Enfoque principal en los factores: {', '.join(factores_top)} "
                f"ya que muestran el mayor impacto estadísticamente significativo."
            )
        
        interacciones_top = list(resumen_significancia.get('interacciones_importantes', {}).keys())[:2]
        if interacciones_top:
            recomendaciones.append(
                f"Considerar las interacciones: {', '.join(interacciones_top)} "
                f"para estrategias de optimización más sofisticadas."
            )
        
        variables_sensibles = list(resumen_significancia.get('variables_mas_sensibles', {}).keys())[:2]
        if variables_sensibles:
            recomendaciones.append(
                f"Las métricas {', '.join(variables_sensibles)} son las más sensibles "
                f"a cambios en los factores experimentales y requieren monitoreo continuo."
            )
        
        return recomendaciones


# ============================================================================
# COMANDOS CLI PRINCIPALES
# ============================================================================

@app.command()
def stats(
    results_dir: Path = typer.Argument(..., help="Directorio con resultados de simulación"),
    output_path: Path = typer.Option("analysis_stats.json", help="Archivo de salida para estadísticas"),
    format_output: str = typer.Option("json", help="Formato de salida: json, csv, excel")
) -> None:
    """
    Análisis estadístico cuantitativo y de sensibilidad sobre KPIs agregados.
    """
    typer.echo(f"🔍 Analizando estadísticas en: {results_dir}")
    
    if not results_dir.exists():
        typer.echo(f"❌ Directorio no encontrado: {results_dir}", err=True)
        raise typer.Exit(1)
    
    try:
        # Recopilar archivos de resultados
        result_files = list(results_dir.glob("*.parquet"))
        if not result_files:
            result_files = list(results_dir.glob("*.json"))
        
        if not result_files:
            typer.echo("❌ No se encontraron archivos de resultados", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"📁 Encontrados {len(result_files)} archivos de resultados")
        
        # Procesar archivos y extraer KPIs
        all_kpis = []
        metadata_list = []
        
        for file_path in result_files:
            try:
                if file_path.suffix == '.parquet':
                    df_eventos = pd.read_parquet(file_path)
                    
                    metadata_file = file_path.with_suffix('.json')
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        metadata_list.append(metadata)
                    
                    kpis = calcular_kpis_desde_eventos(df_eventos)
                    kpis['simulation_file'] = file_path.name
                    all_kpis.append(kpis)
                    
                else:  # JSON
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if 'metricas_entidades' in data:
                        kpis = extraer_kpis_desde_json(data)
                        kpis['simulation_file'] = file_path.name
                        all_kpis.append(kpis)
                        metadata_list.append(data.get('metadatos', {}))
                
            except Exception as e:
                logger.warning(f"Error procesando {file_path}: {e}")
                continue
        
        if not all_kpis:
            typer.echo("❌ No se pudieron extraer KPIs de los archivos", err=True)
            raise typer.Exit(1)
        
        df_kpis = pd.DataFrame(all_kpis)
        
        # Análisis estadístico
        stats_analysis = realizar_analisis_estadistico(df_kpis)
        
        # Análisis de sensibilidad
        sensitivity_analysis = realizar_analisis_sensibilidad(df_kpis, metadata_list)
        
        # Compilar resultados
        results = {
            'resumen_ejecucion': {
                'total_simulaciones': len(all_kpis),
                'archivos_procesados': len(result_files),
                'kpis_analizados': list(df_kpis.select_dtypes(include=[np.number]).columns)
            },
            'estadisticas_descriptivas': stats_analysis,
            'analisis_sensibilidad': sensitivity_analysis,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        # Guardar resultados
        guardar_resultados_stats(results, output_path, format_output)
        
        typer.echo(f"✅ Análisis de estadísticas completado")
        typer.echo(f"📄 Resultados guardados en: {output_path}")
        
        # Mostrar resumen
        mostrar_resumen_stats(stats_analysis)
        
    except Exception as e:
        typer.echo(f"❌ Error en análisis de estadísticas: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def cluster(
    results_dir: Path = typer.Argument(..., help="Directorio con logs de simulaciones fallidas"),
    output_dir: Path = typer.Option("clustering_results", help="Directorio de salida para resultados"),
    algorithm: str = typer.Option("dbscan", help="Algoritmo de clustering: dbscan, kmeans"),
    vectorization: str = typer.Option("tfidf", help="Método de vectorización: tfidf, count, binary"),
    min_failure_events: int = typer.Option(5, help="Mínimo de eventos de fallo por simulación")
) -> None:
    """
    Clustering de arquetipos de fallo usando técnicas avanzadas de ML.
    """
    typer.echo(f"🤖 Iniciando clustering de arquetipos de fallo")
    typer.echo(f"📁 Directorio de resultados: {results_dir}")
    typer.echo(f"🔧 Algoritmo: {algorithm}, Vectorización: {vectorization}")
    
    if not results_dir.exists():
        typer.echo(f"❌ Directorio no encontrado: {results_dir}", err=True)
        raise typer.Exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Extraer secuencias de eventos de fallo
        typer.echo("🔍 Extrayendo secuencias de eventos de fallo...")
        secuencias_fallo = extraer_secuencias_fallo(results_dir, min_failure_events)
        
        if len(secuencias_fallo) < 2:
            typer.echo(f"❌ Muy pocas secuencias de fallo encontradas: {len(secuencias_fallo)}", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"📊 Encontradas {len(secuencias_fallo)} secuencias de fallo")
        
        # Inicializar clusterizador
        clusterizador = ClusterizadorFallos()
        
        # Preparar datos
        typer.echo("🔄 Vectorizando secuencias...")
        feature_matrix = clusterizador.preparar_datos_secuencias(secuencias_fallo, vectorization)
        
        # Aplicar algoritmo de clustering
        typer.echo(f"🎯 Aplicando {algorithm.upper()}...")
        
        if algorithm.lower() == 'dbscan':
            # Optimizar parámetros de DBSCAN
            eps_values = [0.3, 0.5, 0.7, 0.9]
            min_samples_values = [2, 3, 5]
            
            best_result = None
            best_score = -1
            
            for eps in eps_values:
                for min_samples in min_samples_values:
                    try:
                        result = clusterizador.clustering_dbscan(eps, min_samples)
                        score = result.get('silhouette_score', -1)
                        
                        if score is not None and score > best_score:
                            best_score = score
                            best_result = result
                    except:
                        continue
            
            if best_result is None:
                clustering_result = clusterizador.clustering_dbscan()
            else:
                clustering_result = best_result
                
        elif algorithm.lower() == 'kmeans':
            clustering_result = clusterizador.clustering_kmeans()
        else:
            typer.echo(f"❌ Algoritmo no soportado: {algorithm}", err=True)
            raise typer.Exit(1)
        
        # Generar embedding 2D para visualización
        typer.echo("📈 Generando embedding 2D...")
        try:
            embedding_2d = clusterizador.generar_embedding_2d('tsne')
            clustering_result['embedding_2d'] = embedding_2d.tolist()
        except Exception as e:
            logger.warning(f"No se pudo generar embedding 2D: {e}")
            clustering_result['embedding_2d'] = None
        
        # Guardar resultados
        results_file = output_dir / f"clustering_{algorithm}_{vectorization}.json"
        
        clustering_result_serializable = serializar_para_json(clustering_result)
        
        with open(results_file, 'w') as f:
            json.dump({
                'clustering_results': clustering_result_serializable,
                'secuencias_analizadas': len(secuencias_fallo),
                'parametros': {
                    'algorithm': algorithm,
                    'vectorization': vectorization,
                    'min_failure_events': min_failure_events
                },
                'timestamp': pd.Timestamp.now().isoformat()
            }, f, indent=2)
        
        # Guardar secuencias por cluster
        guardar_secuencias_por_cluster(
            secuencias_fallo, 
            clustering_result['labels'], 
            output_dir / f"secuencias_por_cluster_{algorithm}.json"
        )
        
        typer.echo("✅ Clustering completado exitosamente")
        typer.echo(f"📄 Resultados guardados en: {results_file}")
        
        # Mostrar resumen
        mostrar_resumen_clustering(clustering_result)
        
    except Exception as e:
        typer.echo(f"❌ Error en clustering: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def graph(
    results_dir: Path = typer.Argument(..., help="Directorio con resultados de simulación"),
    output_dir: Path = typer.Option("graph_analysis", help="Directorio de salida"),
    max_sequences: int = typer.Option(100, help="Máximo número de secuencias a analizar"),
    top_paths: int = typer.Option(10, help="Número de caminos críticos a reportar")
) -> None:
    """
    Análisis avanzado de grafos de transición usando el kernel optimizado en C.
    """
    typer.echo(f"📊 Iniciando análisis de grafos de transición")
    typer.echo(f"🔧 Kernel en C + NetworkX para análisis optimizado")
    
    if not results_dir.exists():
        typer.echo(f"❌ Directorio no encontrado: {results_dir}", err=True)
        raise typer.Exit(1)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        analizador = AnalizadorSecuencias()
        
        typer.echo("🔍 Extrayendo secuencias de eventos...")
        secuencias_eventos = extraer_secuencias_eventos(results_dir, max_sequences)
        
        if not secuencias_eventos:
            typer.echo("❌ No se encontraron secuencias de eventos", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"📊 Analizando {len(secuencias_eventos)} secuencias")
        
        grafos_resultados = []
        
        with typer.progressbar(secuencias_eventos, label="Procesando secuencias") as progress:
            for i, secuencia in enumerate(progress):
                try:
                    secuencia_codificada = codificar_eventos_como_enteros(secuencia)
                    
                    grafo = analizador.construir_grafo_transicion(secuencia_codificada)
                    
                    if grafo.number_of_nodes() == 0:
                        continue
                    
                    centralidad = analizador.analizar_centralidad(grafo)
                    caminos_criticos = analizador.encontrar_caminos_criticos(grafo, top_paths)
                    
                    resultado = {
                        'sequence_id': f"seq_{i:04d}",
                        'num_nodes': grafo.number_of_nodes(),
                        'num_edges': grafo.number_of_edges(),
                        'has_cycles': grafo.graph.get('has_cycles', False),
                        'centralidad': centralidad,
                        'caminos_criticos': caminos_criticos,
                        'eventos_originales': secuencia[:10]
                    }
                    
                    grafos_resultados.append(resultado)
                    
                except Exception as e:
                    logger.warning(f"Error procesando secuencia {i}: {e}")
                    continue
        
        if not grafos_resultados:
            typer.echo("❌ No se pudieron analizar las secuencias", err=True)
            raise typer.Exit(1)
        
        # Análisis agregado
        typer.echo("📊 Realizando análisis agregado...")
        analisis_agregado = realizar_analisis_agregado_grafos(grafos_resultados)
        
        # Crear grafo agregado
        typer.echo("🔗 Construyendo grafo agregado...")
        grafo_agregado = construir_grafo_agregado(secuencias_eventos, analizador)
        
        if grafo_agregado.number_of_nodes() > 0:
            centralidad_agregada = analizador.analizar_centralidad(grafo_agregado)
            caminos_criticos_agregados = analizador.encontrar_caminos_criticos(
                grafo_agregado, top_paths * 2
            )
            
            analisis_agregado['grafo_completo'] = {
                'num_nodes': grafo_agregado.number_of_nodes(),
                'num_edges': grafo_agregado.number_of_edges(),
                'has_cycles': grafo_agregado.graph.get('has_cycles', False),
                'centralidad': centralidad_agregada,
                'caminos_criticos': caminos_criticos_agregados
            }
        
        # Compilar resultados finales
        resultados_finales = {
            'resumen_ejecucion': {
                'total_secuencias_analizadas': len(grafos_resultados),
                'total_secuencias_procesadas': len(secuencias_eventos),
                'max_sequences_limit': max_sequences,
                'top_paths_analyzed': top_paths
            },
            'analisis_individual': grafos_resultados,
            'analisis_agregado': analisis_agregado,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        # Guardar resultados
        output_file = output_dir / "graph_analysis_results.json"
        with open(output_file, 'w') as f:
            json.dump(serializar_para_json(resultados_finales), f, indent=2)
        
        # Guardar grafo agregado
        if 'grafo_completo' in analisis_agregado:
            grafo_file = output_dir / "grafo_agregado.gexf"
            nx.write_gexf(grafo_agregado, grafo_file)
            typer.echo(f"📈 Grafo agregado guardado en: {grafo_file}")
        
        typer.echo("✅ Análisis de grafos completado exitosamente")
        typer.echo(f"📄 Resultados guardados en: {output_file}")
        
        # Mostrar resumen
        mostrar_resumen_grafos(analisis_agregado)
        
    except Exception as e:
        typer.echo(f"❌ Error en análisis de grafos: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def stats_anova(
    results_dir: Path = typer.Argument(..., help="Directorio con resultados experimentales"),
    output_path: Path = typer.Option("anova_analysis.json", help="Archivo de salida"),
    factores: str = typer.Option("", help="Factores separados por coma"),
    alpha: float = typer.Option(0.05, help="Nivel de significancia para ANOVA")
) -> None:
    """
    Análisis ANOVA factorial avanzado para identificar factores significativos.
    """
    
    typer.echo("🔬 Iniciando análisis ANOVA factorial avanzado")
    
    if not results_dir.exists():
        typer.echo(f"❌ Directorio no encontrado: {results_dir}", err=True)
        raise typer.Exit(1)
    
    try:
        # Cargar datos experimentales
        typer.echo("📊 Cargando datos experimentales...")
        df_resultados = cargar_datos_experimentales(results_dir)
        
        if df_resultados.empty:
            typer.echo("❌ No se encontraron datos válidos para análisis", err=True)
            raise typer.Exit(1)
        
        typer.echo(f"✅ Datos cargados: {len(df_resultados)} experimentos")
        
        # Procesar factores
        if factores:
            lista_factores = [f.strip() for f in factores.split(',')]
        else:
            lista_factores = auto_detectar_factores(df_resultados)
        
        variables_respuesta = auto_detectar_variables_respuesta(df_resultados)
        
        typer.echo(f"🔧 Factores identificados: {lista_factores}")
        typer.echo(f"📈 Variables de respuesta: {variables_respuesta}")
        
        # Realizar análisis ANOVA
        analizador = AnalizadorANOVA(alpha=alpha)
        resultados_anova = analizador.analisis_factorial_completo(
            df_resultados, lista_factores, variables_respuesta
        )
        
        # Guardar resultados
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializar_para_json(resultados_anova), f, indent=2, ensure_ascii=False)
        
        typer.echo("✅ Análisis ANOVA completado exitosamente")
        typer.echo(f"📄 Resultados guardados en: {output_path}")
        
        # Mostrar resumen
        mostrar_resumen_anova(resultados_anova)
        
    except Exception as e:
        typer.echo(f"❌ Error en análisis ANOVA: {e}", err=True)
        raise typer.Exit(1)


# ============================================================================
# FUNCIONES DE UTILIDAD Y PROCESAMIENTO
# ============================================================================

def calcular_kpis_desde_eventos(df_eventos: pd.DataFrame) -> Dict[str, float]:
    """Calcula KPIs principales desde DataFrame de eventos."""
    if df_eventos.empty:
        return {}
    
    kpis = {}
    
    try:
        # KPIs básicos
        kpis['total_eventos'] = len(df_eventos)
        
        # Manejo de timestamps
        if 'timestamp' in df_eventos.columns:
            try:
                df_eventos['timestamp'] = pd.to_datetime(df_eventos['timestamp'])
                duracion = (df_eventos['timestamp'].max() - df_eventos['timestamp'].min()).total_seconds() / 3600
                kpis['duracion_simulacion'] = duracion
                kpis['eventos_por_hora'] = kpis['total_eventos'] / max(duracion, 0.001)
            except:
                kpis['duracion_simulacion'] = 0
                kpis['eventos_por_hora'] = 0
        
        # KPIs por tipo de evento
        if 'event_type' in df_eventos.columns:
            eventos_por_tipo = df_eventos['event_type'].value_counts()
            for evento_tipo, count in eventos_por_tipo.items():
                kpis[f'eventos_{evento_tipo}'] = count
            
            # KPIs de disrupciones
            eventos_disrupcion = df_eventos[df_eventos['event_type'].str.contains('disrupcion|fallo|error', case=False, na=False)]
            kpis['total_disrupciones'] = len(eventos_disrupcion)
            
            if kpis.get('duracion_simulacion', 0) > 0:
                kpis['tasa_disrupciones'] = kpis['total_disrupciones'] / kpis['duracion_simulacion']
            else:
                kpis['tasa_disrupciones'] = 0
        
    except Exception as e:
        logger.warning(f"Error calculando KPIs: {e}")
    
    return kpis


def extraer_kpis_desde_json(data: Dict[str, Any]) -> Dict[str, float]:
    """Extrae KPIs desde estructura JSON de resultados."""
    kpis = {}
    
    try:
        if 'metricas_entidades' in data:
            metricas = data['metricas_entidades']
            
            for entidad_id, metricas_entidad in metricas.items():
                if isinstance(metricas_entidad, dict):
                    for metrica, valor in metricas_entidad.items():
                        if isinstance(valor, (int, float)):
                            kpi_name = f"{entidad_id}_{metrica}"
                            kpis[kpi_name] = valor
        
        if 'metadatos' in data and 'configuracion' in data['metadatos']:
            config = data['metadatos']['configuracion']
            kpis['duracion_configurada'] = config.get('simulacion', {}).get('duracion', 0)
            kpis['numero_camiones'] = len(config.get('entidades', {}))
    
    except Exception as e:
        logger.warning(f"Error extrayendo KPIs de JSON: {e}")
    
    return kpis


def realizar_analisis_estadistico(df_kpis: pd.DataFrame) -> Dict[str, Any]:
    """Realiza análisis estadístico completo de los KPIs."""
    stats = {}
    
    try:
        numeric_cols = df_kpis.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            return {'error': 'No hay columnas numéricas para analizar'}
        
        # Estadísticas descriptivas
        stats['descriptivas'] = {}
        for col in numeric_cols:
            series = df_kpis[col].dropna()
            if len(series) > 0:
                stats['descriptivas'][col] = {
                    'count': int(series.count()),
                    'mean': float(series.mean()),
                    'std': float(series.std()),
                    'min': float(series.min()),
                    'q25': float(series.quantile(0.25)),
                    'median': float(series.median()),
                    'q75': float(series.quantile(0.75)),
                    'max': float(series.max()),
                    'cv': float(series.std() / series.mean()) if series.mean() != 0 else 0
                }
        
        # Matriz de correlación
        if len(numeric_cols) > 1:
            corr_matrix = df_kpis[numeric_cols].corr()
            stats['correlaciones'] = corr_matrix.to_dict()
            
            correlaciones_altas = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if not pd.isna(corr_value) and abs(corr_value) > 0.5:
                        correlaciones_altas.append({
                            'variable1': corr_matrix.columns[i],
                            'variable2': corr_matrix.columns[j],
                            'correlation': float(corr_value)
                        })
            
            stats['correlaciones_altas'] = correlaciones_altas
    
    except Exception as e:
        logger.error(f"Error en análisis estadístico: {e}")
        stats['error'] = str(e)
    
    return stats


def realizar_analisis_sensibilidad(df_kpis: pd.DataFrame, metadata_list: List[Dict]) -> Dict[str, Any]:
    """Realiza análisis de sensibilidad entre parámetros de entrada y KPIs."""
    sensitivity = {}
    
    try:
        if not metadata_list:
            return {'error': 'No hay metadatos para análisis de sensibilidad'}
        
        parametros = []
        for metadata in metadata_list:
            if 'configuracion' in metadata:
                config = metadata['configuracion']
                params = {}
                
                sim_config = config.get('simulacion', {})
                params['duracion'] = sim_config.get('duracion', 0)
                params['numero_camiones'] = len(config.get('entidades', {}))
                
                planta_config = config.get('planta', {})
                params['capacidad_planta'] = planta_config.get('capacidad_maxima', 0)
                
                demanda_config = config.get('demanda', {})
                params['intervalo_demanda'] = demanda_config.get('intervalo_demanda', 24)
                
                parametros.append(params)
        
        if len(parametros) != len(df_kpis):
            logger.warning("Número de parámetros no coincide con KPIs")
            return {'error': 'Inconsistencia entre parámetros y KPIs'}
        
        df_params = pd.DataFrame(parametros)
        
        numeric_kpis = df_kpis.select_dtypes(include=[np.number]).columns
        numeric_params = df_params.select_dtypes(include=[np.number]).columns
        
        if len(numeric_kpis) > 0 and len(numeric_params) > 0:
            sensitivities = []
            
            for param in numeric_params:
                for kpi in numeric_kpis:
                    try:
                        correlation = df_params[param].corr(df_kpis[kpi])
                        if not pd.isna(correlation):
                            sensitivities.append({
                                'parametro': param,
                                'kpi': kpi,
                                'sensibilidad': float(correlation),
                                'sensibilidad_abs': float(abs(correlation))
                            })
                    except:
                        continue
            
            sensitivities.sort(key=lambda x: x['sensibilidad_abs'], reverse=True)
            
            sensitivity['sensibilidades'] = sensitivities[:20]
            
            sensitivity['por_parametro'] = {}
            for param in numeric_params:
                param_sensitivities = [s for s in sensitivities if s['parametro'] == param]
                if param_sensitivities:
                    sensitivity['por_parametro'][param] = {
                        'max_sensibilidad': max(s['sensibilidad_abs'] for s in param_sensitivities),
                        'kpi_mas_sensible': max(param_sensitivities, key=lambda x: x['sensibilidad_abs'])['kpi'],
                        'promedio_sensibilidad': sum(s['sensibilidad_abs'] for s in param_sensitivities) / len(param_sensitivities)
                    }
    
    except Exception as e:
        logger.error(f"Error en análisis de sensibilidad: {e}")
        sensitivity['error'] = str(e)
    
    return sensitivity


def extraer_secuencias_fallo(results_dir: Path, min_events: int) -> List[List[str]]:
    """Extrae secuencias de eventos de simulaciones que tuvieron fallos."""
    secuencias = []
    
    try:
        event_files = list(results_dir.glob("*.parquet"))
        
        for file_path in event_files:
            try:
                df = pd.read_parquet(file_path)
                
                if 'event_type' in df.columns:
                    eventos_fallo = df[
                        df['event_type'].str.contains('disrupcion|fallo|error|quiebre', case=False, na=False)
                    ]
                    
                    if len(eventos_fallo) >= min_events:
                        if 'timestamp' in df.columns:
                            eventos_fallo = eventos_fallo.sort_values('timestamp')
                        
                        secuencia = eventos_fallo['event_type'].tolist()
                        secuencias.append(secuencia)
                        
            except Exception as e:
                logger.warning(f"Error procesando {file_path}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error extrayendo secuencias de fallo: {e}")
    
    return secuencias


def extraer_secuencias_eventos(results_dir: Path, max_sequences: int) -> List[List[str]]:
    """Extrae secuencias de eventos para análisis de grafos."""
    secuencias = []
    
    try:
        event_files = list(results_dir.glob("*.parquet"))[:max_sequences]
        
        for file_path in event_files:
            try:
                df = pd.read_parquet(file_path)
                
                if not df.empty and 'event_type' in df.columns:
                    if 'timestamp' in df.columns:
                        df_sorted = df.sort_values('timestamp')
                    else:
                        df_sorted = df
                    
                    secuencia = df_sorted['event_type'].tolist()
                    
                    if len(secuencia) >= 5:
                        secuencias.append(secuencia)
                        
            except Exception as e:
                logger.warning(f"Error procesando {file_path}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error extrayendo secuencias: {e}")
    
    return secuencias


def codificar_eventos_como_enteros(secuencia: List[str]) -> List[int]:
    """Codifica eventos string como enteros para el kernel en C."""
    eventos_unicos = list(set(secuencia))
    evento_to_int = {evento: i for i, evento in enumerate(eventos_unicos)}
    
    return [evento_to_int[evento] for evento in secuencia]


def serializar_para_json(obj: Any) -> Any:
    """Convierte objetos NumPy y otros tipos no serializables a tipos JSON."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: serializar_para_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serializar_para_json(item) for item in obj]
    else:
        return obj


def guardar_resultados_stats(results: Dict[str, Any], output_path: Path, format_output: str) -> None:
    """Guarda resultados de análisis estadístico en el formato especificado."""
    if format_output.lower() == 'json':
        with open(output_path, 'w') as f:
            json.dump(serializar_para_json(results), f, indent=2)
    elif format_output.lower() == 'csv':
        if 'estadisticas_descriptivas' in results and 'descriptivas' in results['estadisticas_descriptivas']:
            df_stats = pd.DataFrame(results['estadisticas_descriptivas']['descriptivas']).T
            csv_path = output_path.with_suffix('.csv')
            df_stats.to_csv(csv_path)
    elif format_output.lower() == 'excel':
        excel_path = output_path.with_suffix('.xlsx')
        with pd.ExcelWriter(excel_path) as writer:
            if 'estadisticas_descriptivas' in results and 'descriptivas' in results['estadisticas_descriptivas']:
                df_stats = pd.DataFrame(results['estadisticas_descriptivas']['descriptivas']).T
                df_stats.to_excel(writer, sheet_name='Estadisticas_Descriptivas')
            
            if 'analisis_sensibilidad' in results and 'sensibilidades' in results['analisis_sensibilidad']:
                df_sens = pd.DataFrame(results['analisis_sensibilidad']['sensibilidades'])
                df_sens.to_excel(writer, sheet_name='Analisis_Sensibilidad', index=False)


def guardar_secuencias_por_cluster(secuencias: List[List[str]], labels: np.ndarray, output_path: Path) -> None:
    """Guarda las secuencias agrupadas por cluster."""
    clusters = defaultdict(list)
    
    for i, label in enumerate(labels):
        cluster_name = 'noise' if label == -1 else f'cluster_{label}'
        clusters[cluster_name].append({
            'sequence_id': i,
            'events': secuencias[i]
        })
    
    with open(output_path, 'w') as f:
        json.dump(dict(clusters), f, indent=2)


def realizar_analisis_agregado_grafos(grafos_resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Realiza análisis agregado de todos los grafos individuales."""
    if not grafos_resultados:
        return {}
    
    analisis = {}
    
    try:
        num_nodes_list = [r['num_nodes'] for r in grafos_resultados]
        num_edges_list = [r['num_edges'] for r in grafos_resultados]
        has_cycles_list = [r['has_cycles'] for r in grafos_resultados]
        
        analisis['estadisticas_grafos'] = {
            'total_grafos_analizados': len(grafos_resultados),
            'promedio_nodos': float(np.mean(num_nodes_list)),
            'promedio_aristas': float(np.mean(num_edges_list)),
            'porcentaje_con_ciclos': float(sum(has_cycles_list) / len(has_cycles_list) * 100),
            'densidad_promedio': float(np.mean([
                r['num_edges'] / max(r['num_nodes'] * (r['num_nodes'] - 1), 1)
                for r in grafos_resultados if r['num_nodes'] > 1
            ])) if any(r['num_nodes'] > 1 for r in grafos_resultados) else 0
        }
        
        # Análisis de centralidad agregada
        nodos_criticos_todos = []
        for resultado in grafos_resultados:
            if 'centralidad' in resultado and 'nodos_criticos' in resultado['centralidad']:
                nodos_criticos_todos.extend(resultado['centralidad']['nodos_criticos'])
        
        if nodos_criticos_todos:
            contador_nodos = Counter([str(nodo[0]) for nodo in nodos_criticos_todos])
            analisis['nodos_mas_criticos_globalmente'] = contador_nodos.most_common(10)
        
        # Análisis de caminos críticos
        todos_caminos = []
        for resultado in grafos_resultados:
            todos_caminos.extend(resultado.get('caminos_criticos', []))
        
        if todos_caminos:
            longitudes = [c['longitud'] for c in todos_caminos]
            pesos = [c['peso_total'] for c in todos_caminos]
            
            analisis['estadisticas_caminos_criticos'] = {
                'total_caminos_analizados': len(todos_caminos),
                'longitud_promedio': float(np.mean(longitudes)),
                'peso_promedio': float(np.mean(pesos)),
                'longitud_maxima': int(max(longitudes)),
                'peso_maximo': float(max(pesos))
            }
    
    except Exception as e:
        logger.error(f"Error en análisis agregado: {e}")
        analisis['error'] = str(e)
    
    return analisis


def construir_grafo_agregado(secuencias: List[List[str]], analizador: AnalizadorSecuencias) -> nx.DiGraph:
    """Construye un grafo agregado de todas las secuencias."""
    try:
        secuencia_completa = []
        for secuencia in secuencias:
            secuencia_completa.extend(secuencia)
        
        if len(secuencia_completa) > 1:
            secuencia_codificada = codificar_eventos_como_enteros(secuencia_completa)
            return analizador.construir_grafo_transicion(secuencia_codificada)
        
    except Exception as e:
        logger.error(f"Error construyendo grafo agregado: {e}")
    
    return nx.DiGraph()


def cargar_datos_experimentales(results_dir: Path) -> pd.DataFrame:
    """Carga y consolida datos de múltiples experimentos."""
    
    df_consolidado = pd.DataFrame()
    
    archivos_parquet = list(results_dir.glob("*.parquet"))
    
    for archivo in archivos_parquet:
        try:
            df_eventos = pd.read_parquet(archivo)
            
            metadata_file = archivo.with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                config = metadata.get('metadatos', {}).get('configuracion', {})
                
                kpis = calcular_kpis_desde_eventos(df_eventos)
                
                fila_experimento = {**config.get('simulacion', {}), 
                                  **config.get('planta', {}), 
                                  **kpis}
                fila_experimento['archivo_fuente'] = archivo.name
                
                df_consolidado = pd.concat([df_consolidado, pd.DataFrame([fila_experimento])], 
                                         ignore_index=True)
        except Exception as e:
            logger.warning(f"Error procesando {archivo}: {e}")
            continue
    
    return df_consolidado


def auto_detectar_factores(df: pd.DataFrame) -> List[str]:
    """Auto-detecta factores experimentales basado en variabilidad."""
    
    factores_candidatos = []
    
    for col in df.columns:
        if col in ['archivo_fuente']:
            continue
            
        valores_unicos = df[col].nunique()
        if 2 <= valores_unicos <= 10:
            factores_candidatos.append(col)
    
    factores_conocidos = ['numero_camiones', 'capacidad_planta', 'duracion', 'capacidad_camion', 
                         'nivel_critico', 'intervalo_demanda']
    
    factores_finales = []
    for factor in factores_conocidos:
        if factor in factores_candidatos:
            factores_finales.append(factor)
    
    for factor in factores_candidatos:
        if factor not in factores_finales:
            factores_finales.append(factor)
    
    return factores_finales[:6]


def auto_detectar_variables_respuesta(df: pd.DataFrame) -> List[str]:
    """Auto-detecta variables de respuesta (KPIs) numéricas."""
    
    variables_respuesta = []
    
    for col in df.select_dtypes(include=[np.number]).columns:
        if col not in ['numero_camiones', 'capacidad_planta', 'duracion', 'semilla_aleatoria']:
            variables_respuesta.append(col)
    
    return variables_respuesta


def mostrar_resumen_stats(stats_analysis: Dict[str, Any]) -> None:
    """Muestra resumen de análisis estadístico en la terminal."""
    if 'descriptivas' in stats_analysis:
        typer.echo("\n📊 Resumen Estadístico:")
        for kpi, stats in list(stats_analysis['descriptivas'].items())[:5]:
            typer.echo(f"  {kpi}:")
            typer.echo(f"    Media: {stats['mean']:.3f}, Std: {stats['std']:.3f}")
            typer.echo(f"    Rango: [{stats['min']:.3f}, {stats['max']:.3f}]")
    
    if 'correlaciones_altas' in stats_analysis:
        typer.echo(f"\n🔗 Correlaciones altas encontradas: {len(stats_analysis['correlaciones_altas'])}")
        for corr in stats_analysis['correlaciones_altas'][:3]:
            typer.echo(f"  {corr['variable1']} <-> {corr['variable2']}: {corr['correlation']:.3f}")


def mostrar_resumen_clustering(clustering_result: Dict[str, Any]) -> None:
    """Muestra resumen de clustering en la terminal."""
    typer.echo(f"\n🎯 Resultado del Clustering ({clustering_result['algoritmo']}):")
    typer.echo(f"  Clusters encontrados: {clustering_result['n_clusters']}")
    
    if 'n_noise_points' in clustering_result:
        typer.echo(f"  Puntos de ruido: {clustering_result['n_noise_points']}")
    
    if clustering_result.get('silhouette_score'):
        typer.echo(f"  Silhouette Score: {clustering_result['silhouette_score']:.3f}")
    
    if 'cluster_info' in clustering_result:
        typer.echo("\n📋 Información de Clusters:")
        for cluster_name, info in list(clustering_result['cluster_info'].items())[:3]:
            typer.echo(f"  {cluster_name}: {info['size']} elementos ({info['percentage']:.1f}%)")


def mostrar_resumen_grafos(analisis_agregado: Dict[str, Any]) -> None:
    """Muestra resumen de análisis de grafos en la terminal."""
    if 'estadisticas_grafos' in analisis_agregado:
        stats = analisis_agregado['estadisticas_grafos']
        typer.echo(f"\n📈 Análisis de Grafos:")
        typer.echo(f"  Grafos analizados: {stats['total_grafos_analizados']}")
        typer.echo(f"  Promedio nodos: {stats['promedio_nodos']:.1f}")
        typer.echo(f"  Promedio aristas: {stats['promedio_aristas']:.1f}")
        typer.echo(f"  Grafos con ciclos: {stats['porcentaje_con_ciclos']:.1f}%")
    
    if 'nodos_mas_criticos_globalmente' in analisis_agregado:
        typer.echo(f"\n⭐ Nodos más críticos:")
        for nodo, frecuencia in analisis_agregado['nodos_mas_criticos_globalmente'][:3]:
            typer.echo(f"  Nodo {nodo}: {frecuencia} apariciones")


def mostrar_resumen_anova(resultados: Dict[str, Any]) -> None:
    """Muestra resumen ejecutivo del análisis ANOVA."""
    
    resumen = resultados.get('resumen_significancia', {})
    config = resultados.get('configuracion', {})
    
    typer.echo(f"\n🔬 Resumen ANOVA (α = {config.get('alpha', 0.05)}):")
    typer.echo(f"   - Experimentos analizados: {config.get('tamaño_muestra', 0)}")
    typer.echo(f"   - Factores evaluados: {config.get('num_factores', 0)}")
    typer.echo(f"   - Variables de respuesta: {config.get('num_variables_respuesta', 0)}")
    
    factores_influyentes = resumen.get('factores_mas_influyentes', {})
    if factores_influyentes:
        typer.echo(f"\n⭐ Factores más influyentes:")
        for factor, count in list(factores_influyentes.items())[:3]:
            typer.echo(f"   - {factor}: significativo en {count} variables")
    
    interacciones = resumen.get('interacciones_importantes', {})
    if interacciones:
        typer.echo(f"\n🔗 Interacciones significativas:")
        for interaccion, count in list(interacciones.items())[:2]:
            typer.echo(f"   - {interaccion}: detectada en {count} variables")
    
    recomendaciones = resultados.get('recomendaciones', [])
    if recomendaciones:
        typer.echo(f"\n💡 Recomendaciones:")
        for i, recomendacion in enumerate(recomendaciones[:3], 1):
            typer.echo(f"   {i}. {recomendacion}")


if __name__ == "__main__":
    app()