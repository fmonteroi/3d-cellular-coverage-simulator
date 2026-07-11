using UnityEngine;

/// <summary>
/// Copies the static simulation configuration into the active scene components.
/// </summary>
[DefaultExecutionOrder(-2000)]
public class SimulationConfigLoader : MonoBehaviour
{
    public PatternGainReconstructor reconstructor;
    public PropagationSettings propagationSettings;
    public PropagationGridSimulator gridSimulator;
    public PrxVoxelChunkRenderer voxelRenderer;
    public PerformanceSettingsManager performanceSettingsManager;
    public MobileReceiverMetrics campusVehicleReceiver;
    public MobileReceiverMetrics linearVehicleReceiver;
    public MobileReceiverMetrics pedestrianReceiver;

    /// <summary>
    /// Applies menu settings before the simulation scripts start.
    /// </summary>
    void Awake()
    {
        // Applies reconstruction parameters
        if (reconstructor != null)
        {
            reconstructor.method = SimulationConfig.reconstructionMethod;
            reconstructor.k = SimulationConfig.k;
            reconstructor.omniMaxGainDbi = SimulationConfig.omniMaxGainDbi;
        }

        // Applies propagation parameters
        if (propagationSettings != null)
        {
            propagationSettings.txPowerDbm = SimulationConfig.txPowerDbm;
            propagationSettings.frequencyGHz = SimulationConfig.frequencyGHz;
            propagationSettings.bandwidthMHz = SimulationConfig.bandwidthMHz;
            propagationSettings.scenario = SimulationConfig.scenario;
            propagationSettings.environmentType = SimulationConfig.environmentType;
            propagationSettings.lossesModel = SimulationConfig.lossesModel;
            propagationSettings.disableShadowing = SimulationConfig.disableShadowing;
        }

        // Applies grid parameters
        if (gridSimulator != null)
        {
            gridSimulator.gridSizeMeters = SimulationConfig.gridSizeMeters;
            gridSimulator.voxelSizeMeters = SimulationConfig.voxelSizeMeters;
            gridSimulator.includeBuildingCollisions = SimulationConfig.buildingCollisions;
        }

        // Applies heatmap rendering parameters
        if (voxelRenderer != null)
        {
            voxelRenderer.minAlpha = SimulationConfig.minAlpha;
            voxelRenderer.maxAlpha = SimulationConfig.maxAlpha;
            voxelRenderer.alphaExponent = SimulationConfig.alphaExponent;
        }

        // Applies the vehicular gain to the campus vehicle
        if (campusVehicleReceiver != null)
        {
            campusVehicleReceiver.rxGainDbi = SimulationConfig.vehicularRxGainDbi;
        }

        // Applies the vehicular gain to the linear vehicle
        if (linearVehicleReceiver != null)
        {
            linearVehicleReceiver.rxGainDbi = SimulationConfig.vehicularRxGainDbi;
        }

        // Applies the cellular gain to the pedestrian receiver
        if (pedestrianReceiver != null)
        {
            pedestrianReceiver.rxGainDbi = SimulationConfig.cellularRxGainDbi;
        }

        // Applies the selected performance mode
        if (performanceSettingsManager != null)
        {
            performanceSettingsManager.defaultMode = SimulationConfig.performanceMode;
        }
    }
}
