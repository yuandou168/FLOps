import torch
import argparse
import numpy as np
import os

def krum(models, num_neighbors=2):
    """
    Aggregates models using Krum, a robust aggregation technique.
    Args:
        models: List of model state_dicts from clients.
        num_neighbors: Number of closest neighbors to consider (default is 2).
    Returns:
        krum_model: The selected Krum model.
    """
    distances = []

    # Calculate distances between models
    for i, model_i in enumerate(models):
        dists = []
        for j, model_j in enumerate(models):
            if i != j:
                dist = sum([(model_i[key] - model_j[key]).norm().item() for key in model_i])
                dists.append(dist)
        dists.sort()
        distances.append((i, sum(dists[:num_neighbors])))

    # Select the model with the smallest sum of distances to its closest neighbors
    selected_model_index = sorted(distances, key=lambda x: x[1])[0][0]
    return models[selected_model_index]

def load_models(model_paths):
    """
    Loads the model state_dicts from the provided paths.
    Args:
        model_paths: List of file paths for the trained models.
    Returns:
        List of model state_dicts.
    """
    return [torch.load(model_path) for model_path in model_paths]

def save_model(model, path):
    """
    Saves the model state_dict to the given path.
    Args:
        model: Model state_dict.
        path: File path to save the model.
    """
    torch.save(model, path)

def main(trained_model_files, global_model):
    # Load models from client files
    models = load_models(trained_model_files)

    # Perform Krum aggregation
    krum_model = krum(models, num_neighbors=2)

    # Save the aggregated model
    save_model(krum_model, "updated_global_model.pth")

    # Log the aggregation strategy
    with open("aggregation_log.txt", "w") as f:
        f.write("Aggregation Strategy: Krum\n")
        f.write("Selected Krum Model Index: " + str(models.index(krum_model)) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs='+', required=True, help="List of trained models from clients")
    parser.add_argument("--global_model", type=str, required=True, help="Path to global model")
    args = parser.parse_args()

    main(args.models, args.global_model)
