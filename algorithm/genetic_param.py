from generator import FractureCurveGenerator
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Define genetic algorithm parameters
population_size = 10  # Population size
genes_per_param = 5  # Number of genes per parameter
num_params = 5  # Number of parameters
total_genes = genes_per_param * num_params  # Total number of genes per individual
crossover_rate = 0.8  # Crossover rate
mutation_rate = 0.01  # Mutation rate
generations = 10  # Number of generations
param_ranges = [
    (1, 200),  # Length of fiber arrangement in bamboo slips, determining the number of angles to simulate
    (0, 1),  # Range of parameter 2
    (1, 10),  # Fiber length
    (0.001, 0.1),   # combined corrosion
    (100, 1000),  # Years of corrosion
]

# Fitness function
def fitness_function(params):
    # This is a hypothetical fitness calculation, should be replaced with the actual calculation method in practical application
    
    generator = FractureCurveGenerator(int(params[0]), 1, int(params[2]), int(params[3]), int(params[4]))
    vectors = generator.get_fracture_curves(118)
    score = abs(0.100-get_silhouette_score(vectors))
    print(params, score)
    return 1-score

# Calculate the similarity of two data distributions
def get_silhouette_score(fake_list):
    fake_vectors = fake_list
    fake_vectors_data_bottom= fake_vectors[:, 3:4, :].astype(np.float32)
    fake_vectors_data_top= fake_vectors[:, 2:3, :].astype(np.float32)
    fake_list_top = []
    fake_list_bottom = []
    for i in range(118):
        fake_list_top.append(fake_vectors_data_top[i][0])
        fake_list_bottom.append(fake_vectors_data_bottom[i][0])

    real_vectors = np.load("dataset/vector_real_118_patch.npy")
    real_vectors_data_bottom = real_vectors[:, 3:4, :].astype(np.float32)
    real_vectors_data_top = real_vectors[:, 2:3, :].astype(np.float32)
    real_list_top = []
    real_list_bottom = []   
    for i in range(118):
        real_list_top.append(real_vectors_data_top[i][0])
        real_list_bottom.append(real_vectors_data_bottom[i][0])

    # Merge the two sets of data
    data_combined_top = np.vstack((fake_list_top, real_list_top))
    data_combined_bottom = np.vstack((fake_list_bottom, real_list_bottom))

    # Apply t-SNE
    tsne = TSNE(n_components=2, random_state=42)  # n_components=2 for 2D visualization
    data_transformed_top = tsne.fit_transform(data_combined_top)
    data_transformed_bottom = tsne.fit_transform(data_combined_bottom)

    # Example label array
    # Assume the first 118 points are from the fake dataset, the next 118 points are from the real dataset
    labels = np.array([0]*118 + [1]*118)

    # Calculate silhouette score
    silhouette_avg_top = silhouette_score(data_transformed_top, labels)
    silhouette_avg_bottom = silhouette_score(data_transformed_bottom, labels)
    silhouette_avg = (silhouette_avg_top + silhouette_avg_bottom) / 2  

    return silhouette_avg


# Fitness calculation, considering parameter ranges
def fitness(individual):
    params_scaled = [
        param_ranges[i][0] + (int("".join(str(bit) for bit in individual[i*genes_per_param:(i+1)*genes_per_param]), 2) / (2**genes_per_param - 1)) * (param_ranges[i][1] - param_ranges[i][0])
        for i in range(num_params)
    ]
    return fitness_function(params_scaled)

# Selection function
def select(population, fitness_scores):
    probabilities = fitness_scores / fitness_scores.sum()
    selected_indices = np.random.choice(range(population_size), size=population_size, replace=True, p=probabilities)
    return population[selected_indices]

# Crossover function
def crossover(parent1, parent2):
    if np.random.rand() < crossover_rate:
        point = np.random.randint(1, total_genes-1)
        offspring1 = np.concatenate((parent1[:point], parent2[point:]))
        offspring2 = np.concatenate((parent2[:point], parent1[point:]))
        return offspring1, offspring2
    else:
        return parent1, parent2

# Mutation function
def mutate(individual):
    for i in range(total_genes):
        if np.random.rand() < mutation_rate:
            individual[i] = 1 - individual[i]
    return individual

if __name__ == "__main__":

    # Initialize population
    np.random.seed(42)
    population = np.random.randint(2, size=(population_size, total_genes))
    
    # Main loop
    best_fitness_history = []
    with ProcessPoolExecutor() as executor:
        for generation in range(generations):
            # Calculate fitness in parallel
            fitness_scores = list(executor.map(fitness, population))
            fitness_scores = np.array(fitness_scores)
            
            best_fitness_history.append(fitness_scores.max())
            
            # Selection, crossover, and mutation processes remain unchanged
            selected = select(population, fitness_scores)
            offspring = []
            for i in range(0, population_size, 2):
                parent1, parent2 = selected[i], selected[i+1]
                child1, child2 = crossover(parent1, parent2)
                child1 = mutate(child1)
                child2 = mutate(child2)
                offspring.append(child1)
                offspring.append(child2)
            population = np.array(offspring)

    # Results
    best_index = np.argmax(fitness_scores)
    best_individual = population[best_index]
    best_params = [
        param_ranges[i][0] + (int("".join(str(bit) for bit in best_individual[i*genes_per_param:(i+1)*genes_per_param]), 2) / (2**genes_per_param - 1)) * (param_ranges[i][1] - param_ranges[i][0])
        for i in range(num_params)
    ]
    best_fitness = fitness(best_individual)

    best_fitness, best_params