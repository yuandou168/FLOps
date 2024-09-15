import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import argparse
import os
from sklearn.metrics import precision_score, recall_score, f1_score

def load_data(dataset_name="CIFAR10", batch_size=64, shuffle=True, train=True, custom_data_dir=None):
    """
    Load a dataset based on the specified name. Supports CIFAR-10, CIFAR-100, MNIST, and custom datasets.
    Allows customization of batch size, shuffling, and whether to load the training or test set.
    """
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))  # Normalization for single channel datasets
    ])

    if dataset_name == "CIFAR10":
        dataset = datasets.CIFAR10(root='./data', train=train, download=True, transform=transform)
    elif dataset_name == "CIFAR100":
        dataset = datasets.CIFAR100(root='./data', train=train, download=True, transform=transform)
    elif dataset_name == "MNIST":
        dataset = datasets.MNIST(root='./data', train=train, download=True, transform=transform)
    elif dataset_name == "Custom" and custom_data_dir:
        dataset = datasets.ImageFolder(root=os.path.join(custom_data_dir, 'train' if train else 'test'),
                                       transform=transform)
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

    data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
    return data_loader

def compute_metrics(labels, predictions):
    """
    Compute precision, recall, and F1-score.
    """
    precision = precision_score(labels, predictions, average='weighted')
    recall = recall_score(labels, predictions, average='weighted')
    f1 = f1_score(labels, predictions, average='weighted')

    return precision, recall, f1

def train_mobilenet(data_loader, model, criterion, optimizer, epochs=1):
    # Ensure the model is on the CPU
    model = model.to('cpu')

    correct = 0
    total = 0
    running_loss = 0.0
    all_labels = []
    all_preds = []
    
    for epoch in range(epochs):
        for inputs, labels in data_loader:
            inputs, labels = inputs.to('cpu'), labels.to('cpu')

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            # Accuracy calculation
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            running_loss += loss.item()

            all_labels.extend(labels.numpy())
            all_preds.extend(predicted.numpy())

        accuracy = 100 * correct / total
        precision, recall, f1 = compute_metrics(all_labels, all_preds)
        avg_loss = running_loss / len(data_loader)

        print(f"Epoch [{epoch + 1}/{epochs}], Loss: {avg_loss:.4f}, Accuracy: {accuracy:.2f}%, Precision: {precision:.4f}, Recall: {recall:.4f}, F1 Score: {f1:.4f}")
        
    return accuracy, avg_loss, precision, recall, f1

def main(dataset, model_file, batch_size, shuffle, train, epochs, custom_data_dir):
    # Load a pre-trained global model (MobileNetV2) or from an external file
    model = models.mobilenet_v2(weights=None)  # Initialize MobileNetV2 without pre-trained weights
    if os.path.exists(model_file):
        print(f"Loading model from {model_file}")
        model.load_state_dict(torch.load(model_file, map_location=torch.device('cpu')))  # Load the model from external file
    else:
        print(f"Model file {model_file} not found.")
        return

    # Load the dataset based on user input
    data_loader = load_data(dataset_name=dataset, batch_size=batch_size, shuffle=shuffle, train=train, custom_data_dir=custom_data_dir)

    # Define loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01)

    # Train locally on client data
    accuracy, avg_loss, precision, recall, f1 = train_mobilenet(data_loader, model, criterion, optimizer, epochs=epochs)

    # Save the locally trained model (on CPU)
    torch.save(model.state_dict(), "client_trained_model.pth")

    # Save the performance metrics
    with open("client_metrics.txt", "w") as f:
        f.write(f"Accuracy: {accuracy:.2f}%\n")
        f.write(f"Loss: {avg_loss:.4f}\n")
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall: {recall:.4f}\n")
        f.write(f"F1 Score: {f1:.4f}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="CIFAR10", help="Dataset to use: CIFAR10, CIFAR100, MNIST, or Custom")
    parser.add_argument("--model", type=str, required=True, help="Path to global model file")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size for the data loader")
    parser.add_argument("--shuffle", type=bool, default=True, help="Whether to shuffle the dataset")
    parser.add_argument("--train", type=bool, default=True, help="Load training or test set")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--custom_data_dir", type=str, default=None, help="Path to the custom dataset folder")
    args = parser.parse_args()

    main(args.dataset, args.model, args.batch_size, args.shuffle, args.train, args.epochs, args.custom_data_dir)
