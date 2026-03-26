# Test "latency_model.py"

from SIMULATOR.src.MODELS.latency_models import LatencyModel

model_parameters = dict({"mu": 70, "beta": 2, "sigma": 1})
t_slot = 0.01
tx_power = 19
assigned_bandwidth = 10
path_loss = 100

latency_model = LatencyModel("LATENCY_MODEL_TEST", model_parameters=model_parameters)
propagation_latency = latency_model.get_propagation_latency(t_slot, tx_power, assigned_bandwidth, path_loss)

print(propagation_latency)
