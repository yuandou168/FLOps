cwlVersion: v1.2
class: CommandLineTool
baseCommand: ["python", "client_train.py"]
hints:
  DockerRequirement:
    dockerPull: username/fl_client_train  # Docker image for client training

inputs:
  model_file:
    type: File
    inputBinding:
      position: 1
      prefix: "--model"
    label: "Global model delivered to the client"

outputs:
  trained_model:
    type: File
    outputBinding:
      glob: "client_trained_model.pth"
    label: "Trained model file for the client"

  client_metrics:
    type: File
    outputBinding:
      glob: "client_metrics.txt"
    label: "Client performance metrics (accuracy, loss)"
