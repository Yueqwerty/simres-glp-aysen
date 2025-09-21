/**
 * sequence_analyzer.c - Kernel de análisis avanzado para secuencias de eventos
 * Implementa algoritmos optimizados para construcción de grafos de transición
 * y análisis de patrones usando técnicas de programación competitiva.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// Estructura para aristas del grafo de transición
typedef struct {
    int from;
    int to;
    int weight;
} Edge;

// Estructura para el grafo de transición
typedef struct {
    Edge* edges;
    int num_edges;
    int capacity;
    int max_node;
} TransitionGraph;

// Hash table para conteo eficiente de transiciones (técnica de leetcode)
#define HASH_SIZE 100007
typedef struct HashNode {
    uint64_t key;  // (from << 32) | to
    int count;
    struct HashNode* next;
} HashNode;

static HashNode* hash_table[HASH_SIZE];

// Función hash usando multiplicación (técnica de hashing competitivo)
static inline int hash_function(uint64_t key) {
    return (key * 2654435761ULL) % HASH_SIZE;
}

// Inicializar hash table
static void init_hash_table(void) {
    memset(hash_table, 0, sizeof(hash_table));
}

// Limpiar hash table
static void clear_hash_table(void) {
    for (int i = 0; i < HASH_SIZE; i++) {
        HashNode* current = hash_table[i];
        while (current) {
            HashNode* temp = current;
            current = current->next;
            free(temp);
        }
        hash_table[i] = NULL;
    }
}

// Insertar/actualizar contador en hash table (técnica de chaining)
static void update_transition_count(int from, int to) {
    uint64_t key = ((uint64_t)from << 32) | (uint64_t)to;
    int hash_idx = hash_function(key);
    
    HashNode* current = hash_table[hash_idx];
    
    // Buscar si ya existe
    while (current) {
        if (current->key == key) {
            current->count++;
            return;
        }
        current = current->next;
    }
    
    // Crear nuevo nodo si no existe
    HashNode* new_node = (HashNode*)malloc(sizeof(HashNode));
    new_node->key = key;
    new_node->count = 1;
    new_node->next = hash_table[hash_idx];
    hash_table[hash_idx] = new_node;
}

// Función principal exportada a Python
TransitionGraph* build_transition_graph(int* sequence, int length, int* result_size) {
    if (!sequence || length <= 1 || !result_size) {
        *result_size = 0;
        return NULL;
    }
    
    // Inicializar estructuras
    init_hash_table();
    
    int max_node = 0;
    
    // Primera pasada: construir hash table de transiciones
    for (int i = 0; i < length - 1; i++) {
        int from = sequence[i];
        int to = sequence[i + 1];
        
        // Actualizar nodo máximo
        if (from > max_node) max_node = from;
        if (to > max_node) max_node = to;
        
        update_transition_count(from, to);
    }
    
    // Contar número total de transiciones únicas
    int unique_transitions = 0;
    for (int i = 0; i < HASH_SIZE; i++) {
        HashNode* current = hash_table[i];
        while (current) {
            unique_transitions++;
            current = current->next;
        }
    }
    
    // Crear grafo de transición
    TransitionGraph* graph = (TransitionGraph*)malloc(sizeof(TransitionGraph));
    graph->edges = (Edge*)malloc(unique_transitions * sizeof(Edge));
    graph->num_edges = 0;
    graph->capacity = unique_transitions;
    graph->max_node = max_node;
    
    // Segunda pasada: llenar array de aristas
    for (int i = 0; i < HASH_SIZE; i++) {
        HashNode* current = hash_table[i];
        while (current) {
            uint64_t key = current->key;
            int from = (int)(key >> 32);
            int to = (int)(key & 0xFFFFFFFF);
            
            graph->edges[graph->num_edges].from = from;
            graph->edges[graph->num_edges].to = to;
            graph->edges[graph->num_edges].weight = current->count;
            graph->num_edges++;
            
            current = current->next;
        }
    }
    
    // Limpiar hash table
    clear_hash_table();
    
    *result_size = graph->num_edges;
    return graph;
}

// Función para liberar memoria del grafo
void free_transition_graph(TransitionGraph* graph) {
    if (graph) {
        if (graph->edges) {
            free(graph->edges);
        }
        free(graph);
    }
}

// Función para obtener matriz de adyacencia (formato denso para NetworkX)
int* get_adjacency_matrix(TransitionGraph* graph, int* matrix_size) {
    if (!graph || graph->max_node < 0) {
        *matrix_size = 0;
        return NULL;
    }
    
    int n = graph->max_node + 1;
    *matrix_size = n;
    
    // Inicializar matriz con ceros
    int* matrix = (int*)calloc(n * n, sizeof(int));
    if (!matrix) {
        *matrix_size = 0;
        return NULL;
    }
    
    // Llenar matriz con pesos de transiciones
    for (int i = 0; i < graph->num_edges; i++) {
        int from = graph->edges[i].from;
        int to = graph->edges[i].to;
        int weight = graph->edges[i].weight;
        
        matrix[from * n + to] = weight;
    }
    
    return matrix;
}

// Función avanzada: detectar ciclos usando DFS (algoritmo de grafos competitivo)
bool has_cycle_dfs(TransitionGraph* graph, int node, bool* visited, bool* rec_stack) {
    visited[node] = true;
    rec_stack[node] = true;
    
    // Recorrer todas las aristas salientes
    for (int i = 0; i < graph->num_edges; i++) {
        if (graph->edges[i].from == node) {
            int neighbor = graph->edges[i].to;
            
            if (!visited[neighbor] && has_cycle_dfs(graph, neighbor, visited, rec_stack)) {
                return true;
            } else if (rec_stack[neighbor]) {
                return true;
            }
        }
    }
    
    rec_stack[node] = false;
    return false;
}

// Detectar ciclos en el grafo de transición
bool detect_cycles(TransitionGraph* graph) {
    if (!graph || graph->max_node < 0) {
        return false;
    }
    
    int n = graph->max_node + 1;
    bool* visited = (bool*)calloc(n, sizeof(bool));
    bool* rec_stack = (bool*)calloc(n, sizeof(bool));
    
    if (!visited || !rec_stack) {
        free(visited);
        free(rec_stack);
        return false;
    }
    
    bool has_cycle = false;
    
    // Verificar ciclos desde cada nodo no visitado
    for (int i = 0; i <= graph->max_node; i++) {
        if (!visited[i]) {
            if (has_cycle_dfs(graph, i, visited, rec_stack)) {
                has_cycle = true;
                break;
            }
        }
    }
    
    free(visited);
    free(rec_stack);
    return has_cycle;
}

// Función para encontrar caminos más pesados (algoritmo de camino más largo)
typedef struct {
    int* path;
    int length;
    int total_weight;
} HeaviestPath;

HeaviestPath* find_heaviest_paths(TransitionGraph* graph, int max_paths) {
    // Implementación simplificada - en producción sería más completa
    // Usar algoritmo de Bellman-Ford modificado para caminos más largos
    
    if (!graph || max_paths <= 0) {
        return NULL;
    }
    
    HeaviestPath* paths = (HeaviestPath*)malloc(max_paths * sizeof(HeaviestPath));
    
    // Por ahora retornamos estructura vacía - implementación completa requiere más espacio
    for (int i = 0; i < max_paths; i++) {
        paths[i].path = NULL;
        paths[i].length = 0;
        paths[i].total_weight = 0;
    }
    
    return paths;
}

void free_heaviest_paths(HeaviestPath* paths, int count) {
    if (paths) {
        for (int i = 0; i < count; i++) {
            if (paths[i].path) {
                free(paths[i].path);
            }
        }
        free(paths);
    }
}

// Función de utilidad para debugging
void print_graph_info(TransitionGraph* graph) {
    if (!graph) {
        printf("Graph is NULL\n");
        return;
    }
    
    printf("Graph Info:\n");
    printf("  Edges: %d\n", graph->num_edges);
    printf("  Max Node: %d\n", graph->max_node);
    printf("  Capacity: %d\n", graph->capacity);
    
    printf("  Edges detail:\n");
    for (int i = 0; i < graph->num_edges && i < 10; i++) {  // Solo primeras 10
        printf("    %d -> %d (weight: %d)\n", 
               graph->edges[i].from, 
               graph->edges[i].to, 
               graph->edges[i].weight);
    }
    if (graph->num_edges > 10) {
        printf("    ... and %d more edges\n", graph->num_edges - 10);
    }
}