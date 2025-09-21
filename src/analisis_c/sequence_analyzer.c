/**
 * sequence_analyzer.c - Kernel de análisis avanzado para secuencias de eventos
 * Implementa algoritmos optimizados para construcción de grafos de transición
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// Estructura para aristas del grafo
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

// Hash table para conteo eficiente
#define HASH_SIZE 100007
typedef struct HashNode {
    uint64_t key;  // (from << 32) | to
    int count;
    struct HashNode* next;
} HashNode;

static HashNode* hash_table[HASH_SIZE];

// Función hash
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

// Actualizar contador de transición
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
    
    // Crear nuevo nodo
    HashNode* new_node = (HashNode*)malloc(sizeof(HashNode));
    if (!new_node) return;
    
    new_node->key = key;
    new_node->count = 1;
    new_node->next = hash_table[hash_idx];
    hash_table[hash_idx] = new_node;
}

// Función principal exportada a Python
TransitionGraph* build_transition_graph(int* sequence, int length, int* result_size) {
    if (!sequence || length <= 1 || !result_size) {
        if (result_size) *result_size = 0;
        return NULL;
    }
    
    init_hash_table();
    
    int max_node = 0;
    
    // Construir hash table de transiciones
    for (int i = 0; i < length - 1; i++) {
        int from = sequence[i];
        int to = sequence[i + 1];
        
        if (from > max_node) max_node = from;
        if (to > max_node) max_node = to;
        
        update_transition_count(from, to);
    }
    
    // Contar transiciones únicas
    int unique_transitions = 0;
    for (int i = 0; i < HASH_SIZE; i++) {
        HashNode* current = hash_table[i];
        while (current) {
            unique_transitions++;
            current = current->next;
        }
    }
    
    // Crear grafo
    TransitionGraph* graph = (TransitionGraph*)malloc(sizeof(TransitionGraph));
    if (!graph) {
        clear_hash_table();
        *result_size = 0;
        return NULL;
    }
    
    graph->edges = (Edge*)malloc(unique_transitions * sizeof(Edge));
    if (!graph->edges && unique_transitions > 0) {
        free(graph);
        clear_hash_table();
        *result_size = 0;
        return NULL;
    }
    
    graph->num_edges = 0;
    graph->capacity = unique_transitions;
    graph->max_node = max_node;
    
    // Llenar array de aristas
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
    
    clear_hash_table();
    
    *result_size = graph->num_edges;
    return graph;
}

// Liberar memoria del grafo
void free_transition_graph(TransitionGraph* graph) {
    if (graph) {
        if (graph->edges) {
            free(graph->edges);
        }
        free(graph);
    }
}

// Obtener matriz de adyacencia
int* get_adjacency_matrix(TransitionGraph* graph, int* matrix_size) {
    if (!graph || graph->max_node < 0) {
        if (matrix_size) *matrix_size = 0;
        return NULL;
    }
    
    int n = graph->max_node + 1;
    if (matrix_size) *matrix_size = n;
    
    // Crear matriz inicializada con ceros
    int* matrix = (int*)calloc(n * n, sizeof(int));
    if (!matrix) {
        if (matrix_size) *matrix_size = 0;
        return NULL;
    }
    
    // Llenar matriz con pesos
    for (int i = 0; i < graph->num_edges; i++) {
        int from = graph->edges[i].from;
        int to = graph->edges[i].to;
        int weight = graph->edges[i].weight;
        
        if (from >= 0 && from < n && to >= 0 && to < n) {
            matrix[from * n + to] = weight;
        }
    }
    
    return matrix;
}

// DFS para detección de ciclos
bool has_cycle_dfs(TransitionGraph* graph, int node, bool* visited, bool* rec_stack) {
    if (node < 0 || node > graph->max_node) return false;
    
    visited[node] = true;
    rec_stack[node] = true;
    
    // Recorrer aristas salientes
    for (int i = 0; i < graph->num_edges; i++) {
        if (graph->edges[i].from == node) {
            int neighbor = graph->edges[i].to;
            
            if (neighbor < 0 || neighbor > graph->max_node) continue;
            
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

// Detectar ciclos en el grafo
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

// Función de debugging
void print_graph_info(TransitionGraph* graph) {
    if (!graph) {
        printf("Graph is NULL\n");
        return;
    }
    
    printf("Graph Info:\n");
    printf("  Edges: %d\n", graph->num_edges);
    printf("  Max Node: %d\n", graph->max_node);
    printf("  Capacity: %d\n", graph->capacity);
    
    printf("  Edges detail (first 10):\n");
    int show_count = graph->num_edges < 10 ? graph->num_edges : 10;
    for (int i = 0; i < show_count; i++) {
        printf("    %d -> %d (weight: %d)\n", 
               graph->edges[i].from, 
               graph->edges[i].to, 
               graph->edges[i].weight);
    }
    
    if (graph->num_edges > 10) {
        printf("    ... and %d more edges\n", graph->num_edges - 10);
    }
}