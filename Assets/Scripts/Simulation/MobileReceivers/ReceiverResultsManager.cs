using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using UnityEngine;
using Debug = UnityEngine.Debug;


/// <summary>
/// Identifies each mobile receiver used for result export settings.
/// </summary>
public enum ReceiverType
{
    CampusVehicle,
    LinearVehicle,
    Pedestrian
}


/// <summary>
/// Groups one receiver with its export state and collected samples.
/// </summary>
[Serializable]
public class ReceiverResultsTarget
{
    public ReceiverType receiverType;
    public MobileReceiverMetrics receiver;

    [HideInInspector]
    public bool exported;

    [HideInInspector]
    public List<ReceiverMetricsSnapshot> samples = new List<ReceiverMetricsSnapshot>();

    /// <summary>
    /// Gets the mover attached to the receiver object.
    /// </summary>
    public WaypointMover GetMover()
    {
        if (receiver == null)
        {
            return null;
        }

        return receiver.GetComponent<WaypointMover>();
    }
}


/// <summary>
/// Collects receiver samples and exports CSV files, graphs and configuration data.
/// </summary>
public class ReceiverResultsManager : MonoBehaviour
{
    public PatternGainReconstructor patternReconstructor;
    public Transform emissionPoint;
    public List<ReceiverResultsTarget> targets = new List<ReceiverResultsTarget>();

    private bool recording;
    private string resultsDirectory;

    /// <summary>
    /// Creates the results folder and subscribes to route completion events.
    /// </summary>
    void Start()
    {
        string buildDirectory = Directory.GetParent(Application.dataPath).FullName;

        resultsDirectory = Path.Combine(buildDirectory, "Results", DateTime.Now.ToString("dd-MM-yyyy_HH-mm-ss"));

        Directory.CreateDirectory(resultsDirectory);

        SaveSimulationConfiguration();
        ExportReconstructedPattern();

        for (int i = 0; i < targets.Count; i++)
        {
            WaypointMover mover = targets[i].GetMover();

            if (mover != null)
            {
                mover.OnFirstLapCompleted += OnFirstLapCompleted;
            }
        }
    }

    /// <summary>
    /// Exports unfinished receiver results when the application closes.
    /// </summary>
    void OnApplicationQuit()
    {
        ExportPending();
    }

    /// <summary>
    /// Unsubscribes route events and exports pending results.
    /// </summary>
    void OnDestroy()
    {
        for (int i = 0; i < targets.Count; i++)
        {
            WaypointMover mover = targets[i].GetMover();

            if (mover != null)
            {
                mover.OnFirstLapCompleted -= OnFirstLapCompleted;
            }
        }

        ExportPending();
    }

    /// <summary>
    /// Enables receiver sample storage after the live system is ready.
    /// </summary>
    public void BeginRecording()
    {
        recording = true;
    }

    /// <summary>
    /// Stores one receiver snapshot if recording is active.
    /// </summary>
    public void RecordSnapshot(MobileReceiverMetrics receiver, ReceiverMetricsSnapshot snapshot)
    {
        if (!recording)
        {
            return;
        }

        ReceiverResultsTarget target = FindTarget(receiver);

        if (target == null || target.exported)
        {
            return;
        }

        target.samples.Add(snapshot);
    }

    /// <summary>
    /// Finds the export target linked to a receiver.
    /// </summary>
    private ReceiverResultsTarget FindTarget(MobileReceiverMetrics receiver)
    {
        for (int i = 0; i < targets.Count; i++)
        {
            if (targets[i].receiver == receiver)
            {
                return targets[i];
            }
        }

        return null;
    }

    /// <summary>
    /// Exports the target linked to the mover that completed its route.
    /// </summary>
    private void OnFirstLapCompleted(WaypointMover mover)
    {
        for (int i = 0; i < targets.Count; i++)
        {
            if (targets[i].GetMover() == mover)
            {
                ExportTarget(targets[i]);
                return;
            }
        }
    }

    /// <summary>
    /// Writes the CSV file and starts graph generation for one receiver.
    /// </summary>
    private void ExportTarget(ReceiverResultsTarget target)
    {
        if (target == null || target.exported)
        {
            return;
        }

        if (target.samples.Count == 0)
        {
            return;
        }


        string receiverName = target.receiver.receiverId;

        string csvPath = Path.Combine(resultsDirectory, receiverName + ".csv");


        using (StreamWriter writer = new StreamWriter(csvPath))
        {
            writer.WriteLine(
                "timeSeconds,distanceMeters,prxDbm,snrDb," +
                "worldX,worldY,worldZ,txGainDbi," +
                "pathLossDb,buildingCollisions"
            );

            float initialTime = target.samples[0].timeSeconds;

            for (int i = 0; i < target.samples.Count; i++)
            {
                ReceiverMetricsSnapshot sample = target.samples[i];

                writer.WriteLine(string.Join(",",
                    FormatExport(sample.timeSeconds - initialTime, 3),
                    FormatExport(sample.distanceMeters, 3),
                    FormatExport(sample.prxDbm, 3),
                    FormatExport(sample.snrDb, 3),
                    FormatExport(sample.worldPosition.x, 3),
                    FormatExport(sample.worldPosition.y, 3),
                    FormatExport(sample.worldPosition.z, 3),
                    FormatExport(sample.txGainDbi, 3),
                    FormatExport(sample.pathLossDb, 3),
                    sample.buildingCollisions
                ));
            }
        }

        ReceiverGraphOptions options = GetOptions(target.receiverType);

        StartGraphGenerator(csvPath, receiverName, options);
        target.exported = true;

        Debug.Log("Results exported to: " + resultsDirectory);
    }


    /// <summary>
    /// Formats float values with invariant culture for command arguments.
    /// </summary>
    private string Format(float value)
    {
        return value.ToString("R", CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Formats exported values with the selected number of decimals.
    /// </summary>
    private string FormatExport(float value, int decimals)
    {
        return value.ToString("F" + decimals, CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Gets the selected graph options for one receiver type.
    /// </summary>
    private ReceiverGraphOptions GetOptions(ReceiverType receiverType)
    {
        if (receiverType == ReceiverType.CampusVehicle)
        {
            return SimulationConfig.campusVehicleGraphs;
        }

        if (receiverType == ReceiverType.LinearVehicle)
        {
            return SimulationConfig.linearVehicleGraphs;
        }

        return SimulationConfig.pedestrianGraphs;
    }


    /// <summary>
    /// Starts the Python graph generator for one exported CSV file.
    /// </summary>
    private void StartGraphGenerator(string csvPath, string receiverName, ReceiverGraphOptions options)
    {
        string pythonPath = Path.Combine(Application.streamingAssetsPath, "PythonRuntime", "python.exe");
        string scriptPath = Path.Combine(Application.streamingAssetsPath, "SimulatorBridge", "generate_receiver_graphs.py");

        string arguments = "\"" + scriptPath + "\""
        + " --csv \"" + csvPath + "\""
        + " --output \"" + resultsDirectory + "\""
        + " --receiver \"" + receiverName + "\""
        + " --excellent-threshold " + Format(SimulationConfig.excellentSnrThresholdDb)
        + " --good-threshold " + Format(SimulationConfig.goodSnrThresholdDb)
        + " --poor-threshold " + Format(SimulationConfig.poorSnrThresholdDb);

        if (options.prxDistance)
        {
            arguments += " --prx-distance";
        }

        if (options.snrDistance)
        {
            arguments += " --snr-distance";
        }

        if (options.snrTime)
        {
            arguments += " --snr-time";
        }

        ProcessStartInfo startInfo = new ProcessStartInfo();

        startInfo.FileName = pythonPath;
        startInfo.Arguments = arguments;
        startInfo.UseShellExecute = false;
        startInfo.CreateNoWindow = true;

        try
        {
            Process.Start(startInfo);
        }
        catch (Exception ex)
        {
            Debug.LogError("Could not start graph generator: " + ex.Message);
        }
    }

    /// <summary>
    /// Exports every receiver that has not been exported yet.
    /// </summary>
    public void ExportPending()
    {
        for (int i = 0; i < targets.Count; i++)
        {
            ExportTarget(targets[i]);
        }
    }

    /// <summary>
    /// Exports the reconstructed antenna pattern used by this simulation run.
    /// </summary>
    private void ExportReconstructedPattern()
    {
        if (patternReconstructor == null)
        {
            return;
        }

        string filePath = Path.Combine(resultsDirectory, "reconstructed_pattern.csv");

        // Saves the final reconstructed pattern next to the receiver results
        patternReconstructor.ExportGainDbiMatrixCsv(filePath);
    }

    /// <summary>
    /// Writes the configuration used by this simulation run.
    /// </summary>
    private void SaveSimulationConfiguration()
    {
        string filePath = Path.Combine(resultsDirectory, "simulation_config.txt");

        using (StreamWriter writer = new StreamWriter(filePath))
        {
            writer.WriteLine("SIMULATION CONFIGURATION");
            writer.WriteLine("Created: " + DateTime.Now.ToString("dd-MM-yyyy HH:mm:ss"));

            if (emissionPoint != null)
            {
                writer.WriteLine();

                writer.WriteLine("TRANSMITTER ANTENNA");
                writer.WriteLine("Emission point world X: " + FormatExport(emissionPoint.position.x, 3));
                writer.WriteLine("Emission point world Y: " + FormatExport(emissionPoint.position.y, 3));
                writer.WriteLine("Emission point world Z: " + FormatExport(emissionPoint.position.z, 3));
            }

            writer.WriteLine();

            writer.WriteLine("RECONSTRUCTOR");
            writer.WriteLine("Method: " + SimulationConfig.reconstructionMethod);
            if (SimulationConfig.reconstructionMethod == PatternGainReconstructor.ReconstructionMethod.Vasiliadis2005)
            {
                writer.WriteLine("K factor: " + FormatExport(SimulationConfig.k, 3));
            }

            if (SimulationConfig.reconstructionMethod == PatternGainReconstructor.ReconstructionMethod.Omni)
            {
                writer.WriteLine("Omni max gain: " + FormatExport(SimulationConfig.omniMaxGainDbi, 3) + " dBi");
            }

            writer.WriteLine();

            writer.WriteLine("PROPAGATION");
            writer.WriteLine("Tx power: " + FormatExport(SimulationConfig.txPowerDbm, 3) + " dBm");
            writer.WriteLine("Frequency: " + FormatExport(SimulationConfig.frequencyGHz, 3) + " GHz");
            writer.WriteLine("Bandwidth: " + FormatExport(SimulationConfig.bandwidthMHz, 3) + " MHz");
            writer.WriteLine("Losses model: " + SimulationConfig.lossesModel);
            if (SimulationConfig.lossesModel != PropagationSettings.LossesModelType.FSPL)
            {
                writer.WriteLine("Scenario: " + SimulationConfig.scenario);
                writer.WriteLine("Environment: " + SimulationConfig.environmentType);
                writer.WriteLine("Shadowing disabled: " + SimulationConfig.disableShadowing);
            }

            writer.WriteLine();

            writer.WriteLine("GRID");
            writer.WriteLine("Size: " + SimulationConfig.gridSizeMeters + " m");
            writer.WriteLine("Voxel size: " + FormatExport(SimulationConfig.voxelSizeMeters, 0) + " m");
            writer.WriteLine("Building collisions: " + SimulationConfig.buildingCollisions);

            writer.WriteLine();

            writer.WriteLine("RECEIVERS");
            writer.WriteLine("Vehicular gain: " + FormatExport(SimulationConfig.vehicularRxGainDbi, 3) + " dBi");
            writer.WriteLine("Cellular gain: " + FormatExport(SimulationConfig.cellularRxGainDbi, 3) + " dBi");

            writer.WriteLine();

            writer.WriteLine("HEATMAP");
            writer.WriteLine("Minimum alpha: " + FormatExport(SimulationConfig.minAlpha, 2));
            writer.WriteLine("Maximum alpha: " + FormatExport(SimulationConfig.maxAlpha, 2));
            writer.WriteLine("Alpha exponent: " + FormatExport(SimulationConfig.alphaExponent, 2));

            writer.WriteLine();

            writer.WriteLine("PERFORMANCE");
            writer.WriteLine("Mode: " + SimulationConfig.performanceMode);

            writer.WriteLine();

            writer.WriteLine("SNR BOUNDARIES");
            writer.WriteLine("Excellent / Good: " + FormatExport(SimulationConfig.excellentSnrThresholdDb, 0) + " dB");
            writer.WriteLine("Good / Fair: " + FormatExport(SimulationConfig.goodSnrThresholdDb, 0) + " dB");
            writer.WriteLine("Fair / Poor & coverage threshold: " + FormatExport(SimulationConfig.poorSnrThresholdDb, 0) + " dB");
        }
    }
}
