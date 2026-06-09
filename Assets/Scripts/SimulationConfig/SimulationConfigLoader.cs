using UnityEngine;

[DefaultExecutionOrder(-2000)]
public class SimulationConfigLoader : MonoBehaviour
{
    public PatternGainReconstructor reconstructor;
    public PropagationSettings propagationSettings;
    public PropagationGridSimulator gridSimulator;
    public PrxVoxelChunkRenderer voxelRenderer;
    public PerformanceSettingsManager performanceSettingsManager;
    public MobileReceiverMetrics carReceiver;
    public MobileReceiverMetrics humanReceiver;

    void Awake()
    {
        if (reconstructor != null)
        {
            reconstructor.method = SimulationConfig.reconstructionMethod;
            reconstructor.k = SimulationConfig.k;
        }

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

        if (gridSimulator != null)
        {
            gridSimulator.gridSizeMeters = SimulationConfig.gridSizeMeters;
            gridSimulator.voxelSizeMeters = SimulationConfig.voxelSizeMeters;
            gridSimulator.includeBuildingCollisions = SimulationConfig.buildingCollisions;
        }

        if (voxelRenderer != null)
        {
            voxelRenderer.minAlpha = SimulationConfig.minAlpha;
            voxelRenderer.maxAlpha = SimulationConfig.maxAlpha;
            voxelRenderer.alphaExponent = SimulationConfig.alphaExponent;
        }

        if (carReceiver != null)
        {
            carReceiver.rxGainDbi = SimulationConfig.carRxGainDbi;
        }

        if (humanReceiver != null)
        {
            humanReceiver.rxGainDbi = SimulationConfig.humanRxGainDbi;
        }

        if (performanceSettingsManager != null)
        {
            performanceSettingsManager.defaultMode = SimulationConfig.performanceMode;
        }
    }
}