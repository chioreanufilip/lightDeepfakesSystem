import torch
import torch.nn as nn
from torchvision import models, transforms
from facenet_pytorch import MTCNN
from PIL import Image
import os


class DeepfakeDetector:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model("bestModell.pth")
        self.mtcnn = MTCNN(keep_all=False, device=self.device)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

    def _load_model(self, model_path):
        model = models.mobilenet_v3_small(weights=None)
        model.classifier[3] = nn.Linear(model.classifier[3].in_features, 2)

        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            model.to(self.device)
            model.eval()
            print("AI Model successfully loaded!")
        else:
            print(f"Warning: {model_path} not found!")
        return model

    def predict_face(self, face_img):
        input_tensor = self.transform(face_img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            output = self.model(input_tensor)
            probs = torch.nn.functional.softmax(output, dim=1)[0]
            # probs[0] ist  FAKE
            return probs[0].item() * 100