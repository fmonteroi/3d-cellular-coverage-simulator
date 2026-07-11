using UnityEngine;

/// <summary>
/// Stores the menu values that must persist between the menu scene and the simulation scene.
/// </summary>
public static class SimulationConfig
{
    // Reconstructor options
    public static PatternGainReconstructor.ReconstructionMethod reconstructionMethod = PatternGainReconstructor.ReconstructionMethod.Vasiliadis2005;
    public static float k = 2f;
    public static float omniMaxGainDbi = 0f;

    // Propagation settings
    public static float txPowerDbm = 30f;
    public static float frequencyGHz = 1.785f;
    public static float bandwidthMHz = 10f;
    public static PropagationSettings.ScenarioType scenario = PropagationSettings.ScenarioType.Umi;
    public static PropagationSettings.EnvironmentType environmentType = PropagationSettings.EnvironmentType.LOS;
    public static PropagationSettings.LossesModelType lossesModel = PropagationSettings.LossesModelType.FSPL;
    public static bool disableShadowing = true;

    // Grid configuration
    public static Vector3Int gridSizeMeters = new Vector3Int(300, 40, 400);
    public static float voxelSizeMeters = 2f;
    public static bool buildingCollisions = true;

    // Mobile receiver configuration
    public static float vehicularRxGainDbi = 3f;
    public static float cellularRxGainDbi = 0f;

    // Heatmap visualization
    public static float minAlpha = 0.01f;
    public static float maxAlpha = 0.10f;
    public static float alphaExponent = 3f;

    // Performance settings
    public static PerformanceSettingsManager.PerformanceMode performanceMode = PerformanceSettingsManager.PerformanceMode.Low;

    // Result graph options
    public static ReceiverGraphOptions campusVehicleGraphs = new ReceiverGraphOptions(true, true, true);
    public static ReceiverGraphOptions linearVehicleGraphs = new ReceiverGraphOptions(true, true, true);
    public static ReceiverGraphOptions pedestrianGraphs = new ReceiverGraphOptions(true, true, true);

    // SNR boundaries used for the coverage display
    public static float excellentSnrThresholdDb = 20f;
    public static float goodSnrThresholdDb = 13f;
    public static float poorSnrThresholdDb = 0f; // This boundary is also used to calculate coverage percentage

}

/// <summary>
/// Stores which result graphs must be generated for one receiver.
/// </summary>
public class ReceiverGraphOptions
{
    public bool prxDistance;
    public bool snrDistance;
    public bool snrTime;

    /// <summary>
    /// Creates a graph option group with its three enabled states.
    /// </summary>
    public ReceiverGraphOptions(bool prxDistance, bool snrDistance, bool snrTime)
    {
        this.prxDistance = prxDistance;
        this.snrDistance = snrDistance;
        this.snrTime = snrTime;
    }
}
