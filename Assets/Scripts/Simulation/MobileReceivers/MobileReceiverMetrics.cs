using UnityEngine;

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

    public Vector3 GetWorldPosition()
    {
        if (receiverPoint != null)
        {
            return receiverPoint.position;
        }

        return transform.position;
    }

    public void ApplySnapshot(ReceiverMetricsSnapshot snapshot)
    {
        // Store the latest metrics
        currentMetrics = snapshot;
        hasValidMetrics = true;
    }
}
