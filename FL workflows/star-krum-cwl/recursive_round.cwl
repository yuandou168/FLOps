cwlVersion: v1.2
class: Workflow
inputs:
  round_number:
    type: int
    label: "Current round number"
  client_data:
    type: File[]
    label: "Client data files (not used directly)"
  global_model:
    type: File
    label: "Global model from the previous round"

outputs:
  final_model:
    type: File
    outputSource: round_control/final_model
    label: "Final global model after the last round"

steps:
  distribute_model:
    run: distribute_model.cwl
    scatter: client_data
    scatterMethod: dotproduct
    in:
      model_file: global_model
    out: [distributed_model]
    label: "Distribute global model to each client"

  client_training:
    run: client_training.cwl
    scatter: distribute_model/distributed_model
    scatterMethod: dotproduct
    in:
      model_file: distribute_model/distributed_model
    out: [trained_model]
    label: "Train model on each client (VGG16 + CIFAR-10)"

  model_aggregation:
    run: model_aggregation_krum.cwl  # Using Krum-based aggregation
    in:
      trained_models: client_training/trained_model
      global_model: global_model
    out: [updated_model, aggregation_log]
    label: "Aggregate client models using Krum"

  round_control:
    when: $(inputs.round_number > 1)
    run: recursive_round.cwl
    in:
      round_number: $(inputs.round_number - 1)
      global_model: model_aggregation/updated_model
      client_data: client_data
    out: [final_model]
    label: "Proceed to the next round"

  final_model:
    when: $(inputs.round_number == 1)
    source: model_aggregation/updated_model
    label: "Final global model"
