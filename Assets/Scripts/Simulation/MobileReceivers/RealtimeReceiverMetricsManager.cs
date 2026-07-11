using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Requests live metrics for all configured mobile receivers.
/// </summary>
public class RealtimeReceiverMetricsManager : MonoBehaviour
{
    [Header("References")]
    public PropagationSettings settings;
    public PythonBridgeService bridgeService;
    public PropagationGridSimulator gridSimulator;
    public ReceiverResultsManager resultsManager;

    [Header("Receivers")]
    public List<MobileReceiverMetrics> receivers = new List<MobileReceiverMetrics>();

    [Header("Timing")]
    [Min(0.05f)] public float updateIntervalSeconds = 0.2f;

    private float nextUpdateTime = 0f;
    private bool initializationStarted;
    private bool simulationStarted;

    /// <summary>
    /// Stops receiver movement and starts the Python bridge before live requests begin.
    /// </summary>
    void Start()
    {

        // Disables movement of all receivers at the start of the simulation
        for (int i = 0; i < receivers.Count; i++)
        {
            if (receivers[i] == null)
            {
                continue;
            }

            WaypointMover mover = receivers[i].GetComponent<WaypointMover>();

            if (mover != null)
            {
                mover.enabled = false;
            }
        }

        // Starts the shared bridge in advance
        if (bridgeService != null)
        {
            bridgeService.EnsureStarted();
        }
    }

    /// <summary>
    /// Starts receiver metrics after the grid is ready and updates them on a fixed interval.
    /// </summary>
    void Update()
    {
        // Waits until the grid simulation is ready
        if (!simulationStarted)
        {
            if (!initializationStarted && gridSimulator != null && gridSimulator.ResultsReady)
            {
                initializationStarted = true;
                StartCoroutine(StartMobileSimulation());
            }

            return;
        }

        // Waits until the next scheduled request
        if (Time.time < nextUpdateTime)
        {
            return;
        }

        // Schedules the next request
        nextUpdateTime = Time.time + updateIntervalSeconds;

        // Requests and records the current metrics
        RequestMetrics(true);
    }

    /// <summary>
    /// Warms up the mobile request path before movement and recording start.
    /// </summary>
    private IEnumerator StartMobileSimulation()
    {
        // Runs one mobile request without storing its results
        RequestMetrics(false);

        // Continues during the next frame
        yield return null;

        // Enables movement after the warm-up request
        for (int i = 0; i < receivers.Count; i++)
        {
            if (receivers[i] == null)
            {
                continue;
            }

            WaypointMover mover =
                receivers[i].GetComponent<WaypointMover>();

            if (mover != null)
            {
                mover.enabled = true;
            }
        }

        // Starts storing receiver metrics
        if (resultsManager != null)
        {
            resultsManager.BeginRecording();
        }

        // Allows the first recorded request immediately
        nextUpdateTime = Time.time;

        simulationStarted = true;
    }

    /// <summary>
    /// Builds and sends one live metrics request for all mobile receivers.
    /// </summary>
    private void RequestMetrics(bool recordResults)
    {
        if (settings == null || bridgeService == null)
        {
            Debug.LogWarning("RealtimeReceiverMetricsManager: Missing settings or bridge service.");
            return;
        }

        if (!settings.ValidateSetup())
        {
            return;
        }

        if (receivers == null || receivers.Count == 0)
        {
            return;
        }

        BridgeRequestDto request = settings.BuildBaseRequest();
        request.requestType = "mobile_receivers";
        request.voxels = new List<GridVoxelRequestDto>();
        request.receivers = new List<MobileReceiverRequestDto>(receivers.Count);

        for (int i = 0; i < receivers.Count; i++)
        {
            MobileReceiverMetrics receiver = receivers[i];

            if (receiver == null)
            {
                continue;
            }

            // Reads the current receiver position and antenna gain
            Vector3 worldPosition = receiver.GetWorldPosition();
            float txGainDbi = settings.EvaluateTxGainDbi(worldPosition, $"Receiver {receiver.receiverId}");

            // Computes building losses for mobile receivers
            int buildingCollisions = settings.CountBuildingCollisions(worldPosition);
            float buildingLossDb = buildingCollisions * settings.GetLossPerWallDb();

            MobileReceiverRequestDto receiverRequest = new MobileReceiverRequestDto();
            receiverRequest.id = receiver.receiverId;
            receiverRequest.x = worldPosition.x;
            receiverRequest.y = worldPosition.y;
            receiverRequest.z = worldPosition.z;
            receiverRequest.txGainDbi = txGainDbi;
            receiverRequest.rxGainDbi = receiver.rxGainDbi;
            receiverRequest.buildingCollisions = buildingCollisions;
            receiverRequest.buildingLossDb = buildingLossDb;

            request.receivers.Add(receiverRequest);
        }

        BridgeResponseDto response = bridgeService.SendRequest(request);

        if (!string.IsNullOrEmpty(response.error))
        {
            Debug.LogError($"RealtimeReceiverMetricsManager: Python error: {response.error}");
            return;
        }

        ApplyReceiverResults(response.receiverResults, recordResults);
    }

    /// <summary>
    /// Copies Python receiver results into Unity snapshots and optional result storage.
    /// </summary>
    private void ApplyReceiverResults(List<MobileReceiverResultDto> receiverResults, bool recordResults)
    {
        if (receiverResults == null)
        {
            return;
        }

        for (int i = 0; i < receiverResults.Count; i++)
        {
            MobileReceiverResultDto result = receiverResults[i];
            MobileReceiverMetrics receiver = FindReceiverById(result.id);

            if (receiver == null)
            {
                continue;
            }

            ReceiverMetricsSnapshot snapshot = new ReceiverMetricsSnapshot();
            snapshot.timeSeconds = Time.time;
            snapshot.worldPosition = receiver.GetWorldPosition();
            snapshot.txPowerDbm = settings.txPowerDbm;
            snapshot.rxGainDbi = receiver.rxGainDbi;
            snapshot.txGainDbi = result.txGainDbi;
            snapshot.distanceMeters = result.distanceMeters;
            snapshot.buildingCollisions = result.buildingCollisions;
            snapshot.buildingLossDb = result.buildingLossDb;
            snapshot.basePathLossDb = result.basePathLossDb;
            snapshot.pathLossDb = result.pathLossDb;
            snapshot.prxDbm = result.prxDbm;
            snapshot.snrDb = result.snrDb;

            receiver.ApplySnapshot(snapshot);

            // Stores the sample only after the warm-up request
            if (recordResults && resultsManager != null)
            {
                resultsManager.RecordSnapshot(receiver, snapshot);
            }
        }
    }

    /// <summary>
    /// Finds a configured receiver by its serialized identifier.
    /// </summary>
    private MobileReceiverMetrics FindReceiverById(string receiverId)
    {
        for (int i = 0; i < receivers.Count; i++)
        {
            if (receivers[i] != null && receivers[i].receiverId == receiverId)
            {
                return receivers[i];
            }
        }

        return null;
    }
}
