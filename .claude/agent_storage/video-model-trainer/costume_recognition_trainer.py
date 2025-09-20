#!/usr/bin/env python3
"""
Star Wars Costume Recognition Model Training System
Specialized training pipeline for Star Wars character costume recognition
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
import torchvision.models as models
import cv2
import numpy as np
import json
import os
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2

logger = logging.getLogger(__name__)

class StarWarsCostumeDataset(Dataset):
    """Dataset class for Star Wars costume recognition"""

    def __init__(self, data_dir: str, split: str = 'train', transform=None):
        self.data_dir = Path(data_dir)
        self.split = split
        self.transform = transform

        # Star Wars costume classes (validated by Star Wars Expert)
        self.classes = [
            'jedi',           # Jedi robes, lightsaber, traditional brown/beige
            'sith',           # Dark robes, red lightsaber, black clothing
            'rebel_alliance', # Orange pilot suits, rebel insignia
            'stormtrooper',   # White armor, distinctive helmet
            'imperial_officer', # Gray/black uniforms, imperial insignia
            'mandalorian',    # Distinctive armor, helmet designs
            'civilian'        # Regular clothing, no distinctive SW elements
        ]

        self.class_to_idx = {cls: idx for idx, cls in enumerate(self.classes)}
        self.idx_to_class = {idx: cls for cls, idx in self.class_to_idx.items()}

        self.images = []
        self.labels = []
        self.load_data()

    def load_data(self):
        """Load dataset with proper train/val/test splits"""
        split_file = self.data_dir / f"{self.split}_annotations.json"

        if split_file.exists():
            with open(split_file, 'r') as f:
                annotations = json.load(f)

            for annotation in annotations:
                image_path = self.data_dir / annotation['image_path']
                if image_path.exists():
                    self.images.append(str(image_path))
                    self.labels.append(self.class_to_idx[annotation['class']])
        else:
            # Fallback: scan directory structure
            logger.warning(f"Annotation file {split_file} not found, scanning directories")
            self._scan_directory_structure()

        logger.info(f"Loaded {len(self.images)} images for {self.split} split")

    def _scan_directory_structure(self):
        """Scan directory structure when annotations are not available"""
        for class_name in self.classes:
            class_dir = self.data_dir / self.split / class_name
            if class_dir.exists():
                for img_path in class_dir.glob('*.jpg'):
                    self.images.append(str(img_path))
                    self.labels.append(self.class_to_idx[class_name])

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        image_path = self.images[idx]
        label = self.labels[idx]

        # Load image
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if self.transform:
            if isinstance(self.transform, A.Compose):
                # Albumentations transform
                transformed = self.transform(image=image)
                image = transformed['image']
            else:
                # Torchvision transform
                image = Image.fromarray(image)
                image = self.transform(image)

        return image, label

class CostumeRecognitionModel(nn.Module):
    """CNN model for Star Wars costume recognition"""

    def __init__(self, num_classes: int = 7, backbone: str = 'efficientnet_b0', pretrained: bool = True):
        super(CostumeRecognitionModel, self).__init__()
        self.num_classes = num_classes
        self.backbone_name = backbone

        # Load backbone
        if backbone == 'efficientnet_b0':
            self.backbone = models.efficientnet_b0(pretrained=pretrained)
            in_features = self.backbone.classifier[1].in_features
            self.backbone.classifier = nn.Identity()
        elif backbone == 'resnet50':
            self.backbone = models.resnet50(pretrained=pretrained)
            in_features = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        elif backbone == 'mobilenet_v3_small':
            self.backbone = models.mobilenet_v3_small(pretrained=pretrained)
            in_features = self.backbone.classifier[3].in_features
            self.backbone.classifier = nn.Identity()
        else:
            raise ValueError(f"Unsupported backbone: {backbone}")

        # Custom classifier head for Star Wars costumes
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, num_classes)
        )

        # Attention mechanism for costume-specific features
        self.attention = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(in_features, in_features // 16),
            nn.ReLU(),
            nn.Linear(in_features // 16, in_features),
            nn.Sigmoid()
        )

    def forward(self, x):
        # Extract features
        features = self.backbone(x)

        # Apply attention (if we have feature maps)
        if len(features.shape) == 4:  # Feature maps
            attention_weights = self.attention(features)
            features = features * attention_weights.view(-1, features.size(1), 1, 1)
            features = torch.mean(features, dim=[2, 3])  # Global average pooling

        # Classification
        output = self.classifier(features)
        return output

class CostumeTrainer:
    """Training pipeline for costume recognition model"""

    def __init__(self, config: Dict):
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.train_loader = None
        self.val_loader = None
        self.optimizer = None
        self.scheduler = None
        self.criterion = None

        # Training metrics
        self.train_losses = []
        self.val_losses = []
        self.train_accuracies = []
        self.val_accuracies = []

        self.setup_transforms()
        self.setup_model()

    def setup_transforms(self):
        """Setup data augmentation and preprocessing"""
        # Training augmentations - Star Wars specific
        self.train_transform = A.Compose([
            A.Resize(224, 224),
            A.RandomRotate90(p=0.3),
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.4),
            A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1, p=0.3),
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.2),
            A.Blur(blur_limit=3, p=0.1),
            # Costume-specific augmentations
            A.RandomShadow(p=0.2),  # Different lighting conditions
            A.RandomFog(p=0.1),     # Convention hall conditions
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])

        # Validation transforms
        self.val_transform = A.Compose([
            A.Resize(224, 224),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ToTensorV2()
        ])

    def setup_model(self):
        """Initialize model, loss, optimizer, and scheduler"""
        self.model = CostumeRecognitionModel(
            num_classes=len(self.config['classes']),
            backbone=self.config['model']['backbone'],
            pretrained=True
        ).to(self.device)

        # Loss function with class weights for imbalanced data
        if 'class_weights' in self.config:
            weights = torch.tensor(self.config['class_weights']).to(self.device)
            self.criterion = nn.CrossEntropyLoss(weight=weights)
        else:
            self.criterion = nn.CrossEntropyLoss()

        # Optimizer
        self.optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.config['training']['learning_rate'],
            weight_decay=self.config['training']['weight_decay']
        )

        # Learning rate scheduler
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True
        )

    def setup_dataloaders(self, data_dir: str):
        """Setup training and validation dataloaders"""
        # Training dataset
        train_dataset = StarWarsCostumeDataset(
            data_dir=data_dir,
            split='train',
            transform=self.train_transform
        )

        # Validation dataset
        val_dataset = StarWarsCostumeDataset(
            data_dir=data_dir,
            split='val',
            transform=self.val_transform
        )

        # Data loaders
        self.train_loader = DataLoader(
            train_dataset,
            batch_size=self.config['training']['batch_size'],
            shuffle=True,
            num_workers=self.config['training']['num_workers'],
            pin_memory=True
        )

        self.val_loader = DataLoader(
            val_dataset,
            batch_size=self.config['training']['batch_size'],
            shuffle=False,
            num_workers=self.config['training']['num_workers'],
            pin_memory=True
        )

        logger.info(f"Training samples: {len(train_dataset)}")
        logger.info(f"Validation samples: {len(val_dataset)}")

    def train_epoch(self) -> Tuple[float, float]:
        """Train for one epoch"""
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for batch_idx, (images, labels) in enumerate(self.train_loader):
            images, labels = images.to(self.device), labels.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            # Statistics
            running_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            # Log progress
            if batch_idx % 50 == 0:
                logger.info(f'Batch {batch_idx}/{len(self.train_loader)}, '
                          f'Loss: {loss.item():.4f}, '
                          f'Acc: {100.*correct/total:.2f}%')

        epoch_loss = running_loss / len(self.train_loader)
        epoch_acc = 100. * correct / total

        return epoch_loss, epoch_acc

    def validate_epoch(self) -> Tuple[float, float]:
        """Validate for one epoch"""
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for images, labels in self.val_loader:
                images, labels = images.to(self.device), labels.to(self.device)

                outputs = self.model(images)
                loss = self.criterion(outputs, labels)

                running_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        epoch_loss = running_loss / len(self.val_loader)
        epoch_acc = 100. * correct / total

        return epoch_loss, epoch_acc

    def train(self, data_dir: str, num_epochs: int):
        """Complete training pipeline"""
        logger.info("Starting Star Wars costume recognition training...")

        # Setup data
        self.setup_dataloaders(data_dir)

        best_val_acc = 0.0
        patience_counter = 0
        max_patience = self.config['training'].get('early_stopping_patience', 10)

        for epoch in range(num_epochs):
            logger.info(f"\nEpoch {epoch+1}/{num_epochs}")
            logger.info("-" * 50)

            # Training
            train_loss, train_acc = self.train_epoch()
            self.train_losses.append(train_loss)
            self.train_accuracies.append(train_acc)

            # Validation
            val_loss, val_acc = self.validate_epoch()
            self.val_losses.append(val_loss)
            self.val_accuracies.append(val_acc)

            # Learning rate scheduling
            self.scheduler.step(val_loss)

            logger.info(f'Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%')
            logger.info(f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%')

            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                self.save_model('best_costume_model.pt')
                logger.info(f'New best validation accuracy: {best_val_acc:.2f}%')
            else:
                patience_counter += 1

            # Early stopping
            if patience_counter >= max_patience:
                logger.info(f'Early stopping triggered after {epoch+1} epochs')
                break

            # Save checkpoint
            if (epoch + 1) % 10 == 0:
                self.save_model(f'checkpoint_epoch_{epoch+1}.pt')

        logger.info(f"Training completed. Best validation accuracy: {best_val_acc:.2f}%")
        self.plot_training_history()

    def save_model(self, filename: str):
        """Save model checkpoint"""
        save_path = Path("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/models")
        save_path.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'classes': self.config['classes'],
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'train_accuracies': self.train_accuracies,
            'val_accuracies': self.val_accuracies
        }

        torch.save(checkpoint, save_path / filename)
        logger.info(f"Model saved: {save_path / filename}")

    def plot_training_history(self):
        """Plot training curves"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

        # Loss plot
        ax1.plot(self.train_losses, label='Train Loss')
        ax1.plot(self.val_losses, label='Validation Loss')
        ax1.set_title('Training and Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)

        # Accuracy plot
        ax2.plot(self.train_accuracies, label='Train Accuracy')
        ax2.plot(self.val_accuracies, label='Validation Accuracy')
        ax2.set_title('Training and Validation Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        plt.savefig("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/training_history.png")
        plt.close()

    def evaluate_model(self, test_data_dir: str) -> Dict:
        """Comprehensive model evaluation"""
        logger.info("Evaluating model on test set...")

        # Load test dataset
        test_dataset = StarWarsCostumeDataset(
            data_dir=test_data_dir,
            split='test',
            transform=self.val_transform
        )

        test_loader = DataLoader(
            test_dataset,
            batch_size=self.config['training']['batch_size'],
            shuffle=False,
            num_workers=self.config['training']['num_workers']
        )

        self.model.eval()
        all_predictions = []
        all_labels = []
        all_confidences = []

        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(self.device), labels.to(self.device)

                outputs = self.model(images)
                probabilities = torch.softmax(outputs, dim=1)
                confidences, predictions = torch.max(probabilities, 1)

                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
                all_confidences.extend(confidences.cpu().numpy())

        # Classification report
        class_names = self.config['classes']
        report = classification_report(
            all_labels,
            all_predictions,
            target_names=class_names,
            output_dict=True
        )

        # Confusion matrix
        cm = confusion_matrix(all_labels, all_predictions)

        # Plot confusion matrix
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=class_names, yticklabels=class_names)
        plt.title('Star Wars Costume Recognition - Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.tight_layout()
        plt.savefig("/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/confusion_matrix.png")
        plt.close()

        # Calculate per-class metrics
        evaluation_results = {
            'overall_accuracy': report['accuracy'],
            'macro_avg_f1': report['macro avg']['f1-score'],
            'weighted_avg_f1': report['weighted avg']['f1-score'],
            'per_class_metrics': {},
            'confusion_matrix': cm.tolist(),
            'average_confidence': np.mean(all_confidences)
        }

        for i, class_name in enumerate(class_names):
            if str(i) in report:
                evaluation_results['per_class_metrics'][class_name] = {
                    'precision': report[str(i)]['precision'],
                    'recall': report[str(i)]['recall'],
                    'f1-score': report[str(i)]['f1-score'],
                    'support': report[str(i)]['support']
                }

        # Save evaluation results
        results_path = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/evaluation_results.json"
        with open(results_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2)

        logger.info(f"Evaluation completed. Overall accuracy: {evaluation_results['overall_accuracy']:.4f}")
        logger.info(f"Results saved to: {results_path}")

        return evaluation_results

# Training configuration for Star Wars costumes
def get_training_config():
    """Get training configuration for costume recognition"""
    return {
        "classes": [
            "jedi", "sith", "rebel_alliance", "stormtrooper",
            "imperial_officer", "mandalorian", "civilian"
        ],
        "model": {
            "backbone": "efficientnet_b0",  # Optimized for mobile deployment
            "pretrained": True
        },
        "training": {
            "batch_size": 32,
            "learning_rate": 0.001,
            "weight_decay": 0.0001,
            "num_workers": 4,
            "early_stopping_patience": 10
        },
        "data": {
            "image_size": 224,
            "augmentation_probability": 0.8
        }
    }

# Main training script
def main():
    """Main training function"""
    config = get_training_config()
    trainer = CostumeTrainer(config)

    # Dataset path (would be organized by Roboflow)
    data_dir = "/home/rolo/r2ai/.claude/agent_storage/video-model-trainer/datasets/star_wars_costumes"

    # Train model
    trainer.train(data_dir, num_epochs=50)

    # Evaluate model
    evaluation_results = trainer.evaluate_model(data_dir)

    # Convert to TensorRT for deployment
    trainer.export_for_deployment()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()