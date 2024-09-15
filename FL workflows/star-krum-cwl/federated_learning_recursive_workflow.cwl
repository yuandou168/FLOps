cwlVersion: v1.2
class: Workflow
inputs:
  initial_global_model:
    type: File
    label: "Initial global model file (VGG16)"
  num_rounds:
    type: int
    label: "Number of communication rounds"
  client_data:
    type: File[]
    label: "Client data files (optional)"

outputs:
  final_global_model:
    type: File
    outputSource: recursive_workflow/final_model
    label: "Final global model after aggregation"

steps:
  recursive_workflow:
    run: recursive_round.cwl
    in:
      round_number: num_rounds
      global_model: initial_global_model
      client_data: client_data
    out: [final_model]
    label: "Recursive federated learning with Krum"
