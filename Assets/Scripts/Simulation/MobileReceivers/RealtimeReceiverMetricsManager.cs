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

    [Header("Receivers")]
    public List<MobileReceiverMetrics> receivers = new List<MobileReceiverMetrics>();

    [Header("Timing")]
    [Min(0.05f)] public float updateIntervalSeconds = 0.2f;

    float nextUpdateTime = 0f;

    void Start()
    {
        // Start the shared bridge in advance
        if (bridgeService != null)
        {
            bridgeService.EnsureStarted();
        }
    }

    void Update()
    {
        // Wait until the next scheduled update
        if (Time.time < nextUpdateTime)
        {
            return;
        }

        nextUpdateTime = Time.time + updateIntervalSeconds;
        RequestMetrics();
    }

    private void RequestMetrics()
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

            Vector3 worldPosition = receiver.GetWorldPosition();
            float txGainDbi = settings.EvaluateTxGainDbi(worldPosition, $"Receiver {receiver.receiverId}");
            int buildingCollisions = settings.CountBuildingCollisions(worldPosition);
            float buildingLossDb = buildingCollisions * settings.lossPerBuildingDb;

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

        ApplyReceiverResults(response.receiverResults);
    }

    private void ApplyReceiverResults(List<MobileReceiverResultDto> receiverResults)
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
            snapshot.propagationLatencyMs = result.propagationLatencyMs;

            receiver.ApplySnapshot(snapshot);
        }
    }

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
