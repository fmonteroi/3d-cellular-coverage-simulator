using UnityEngine;

public static class SimulationConfig
{
    // Reconstructor Options
    public static PatternGainReconstructor.ReconstructionMethod reconstructionMethod = PatternGainReconstructor.ReconstructionMethod.Vasiliadis2005;
    public static float k = 2f;

    // Propagation Settings
    public static float txPowerDbm = 30f;
    public static float frequencyGHz = 1.785f;
    public static float bandwidthMHz = 10f;
    public static PropagationSettings.ScenarioType scenario = PropagationSettings.ScenarioType.Umi;
    public static PropagationSettings.EnvironmentType environmentType = PropagationSettings.EnvironmentType.LOS;
    public static PropagationSettings.LossesModelType lossesModel = PropagationSettings.LossesModelType.FSPL;
    public static bool disableShadowing = true;

    // Grid Configuration
    public static Vector3Int gridSizeMeters = new Vector3Int(300, 50, 400);
    public static float voxelSizeMeters = 2f;
    public static bool buildingCollisions = true;

    // Mobile Receiver Configuration
    public static float carRxGainDbi = 3f;
    public static float humanRxGainDbi = 0f;

    // Heatmap Visualization
    public static float minAlpha = 0.01f;
    public static float maxAlpha = 0.6f;
    public static float alphaExponent = 5f;

    // Performance Settings
    public static PerformanceSettingsManager.PerformanceMode performanceMode = PerformanceSettingsManager.PerformanceMode.Low;

}
