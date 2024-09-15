cwlVersion: v1.2
class: CommandLineTool
baseCommand: ["cp"]
hints:
  DockerRequirement:
    dockerPull: ubuntu:latest

inputs:
  model_file:
    type: File
    inputBinding:
      position: 1
    label: "Global model to distribute"

outputs:
  distributed_model:
    type: File
    outputBinding:
      glob: "client_model.pth"
    label: "Distributed global model for the client"
