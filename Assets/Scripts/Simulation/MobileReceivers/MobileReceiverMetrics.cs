using UnityEngine;
using System;

/// <summary>
/// Stores the current metrics of one mobile receiver.
/// </summary>
public class MobileReceiverMetrics : MonoBehaviour
{
    public string receiverId = "MR_1";

    [Header("Link budget")]
    public float rxGainDbi = 2f;

    [Header("Receiver point")]
    public Transform receiverPoint;

    [Header("Current metrics")]
    public bool hasValidMetrics = false;
    public ReceiverMetricsSnapshot currentMetrics = new ReceiverMetricsSnapshot();

    // Notifies other components when new receiver metrics arrive
    public event Action<ReceiverMetricsSnapshot> OnMetricsUpdated;

    /// <summary>
    /// Gets the world position used for receiver metric calculations.
    /// </summary>
    public Vector3 GetWorldPosition()
    {
        if (receiverPoint != null)
        {
            return receiverPoint.position;
        }

        return transform.position;
    }

    /// <summary>
    /// Stores a new metrics snapshot and notifies listeners.
    /// </summary>
    public void ApplySnapshot(ReceiverMetricsSnapshot snapshot)
    {
        // Stores the latest metrics
        currentMetrics = snapshot;
        hasValidMetrics = true;

        // Notifies the coverage indicator
        if (OnMetricsUpdated != null)
        {
            OnMetricsUpdated(snapshot);
        }
    }
}
