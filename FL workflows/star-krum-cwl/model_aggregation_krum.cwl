cwlVersion: v1.2
class: CommandLineTool
baseCommand: ["python", "aggregate_models.py"]
hints:
  DockerRequirement:
    dockerPull: username/fl_model_agg  # Docker image with the aggregation script

inputs:
  trained_models:
    type: File[]
    inputBinding:
      position: 1
      prefix: "--models"
    label: "List of trained client models"

  global_model:
    type: File
    inputBinding:
      position: 2
      prefix: "--global_model"
    label: "Global model before aggregation"

outputs:
  updated_model:
    type: File
    outputBinding:
      glob: "updated_global_model.pth"
    label: "Updated global model after aggregation"

  aggregation_log:
    type: File
    outputBinding:
      glob: "aggregation_log.txt"
    label: "Log of Krum aggregation details"
