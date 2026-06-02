using TMPro;
using UnityEngine;

/// <summary>
/// Displays the metrics of the selected mobile receiver.
/// </summary>
public class ReceiverMetricsPanel : MonoBehaviour
{
    public TMP_Text titleText;
    public TMP_Text instructionsText;
    public TMP_Text metricsText;

    MobileReceiverMetrics currentReceiver;

    void Start()
    {
        instructionsText.text = "A / Left: previous    D / Right: next";
    }

    void Update()
    {
        if (currentReceiver == null || !currentReceiver.hasValidMetrics)
        {
            return;
        }

        ReceiverMetricsSnapshot m = currentReceiver.currentMetrics;

        titleText.text = $"Metrics {currentReceiver.receiverId}";

        metricsText.text =
            $"Distance: {m.distanceMeters:F2} m\n" +
            $"Building collisions: {m.buildingCollisions}\n" +
            $"Path loss: {m.pathLossDb:F2} dB\n\n" +
            $"Prx: {m.prxDbm:F2} dBm\n" +
            $"SNR: {m.snrDb:F2} dB\n" +
            $"Propagation Latency: {m.propagationLatencyMs:F6} ms";
    }

    public void HideMetrics()
    {
        currentReceiver = null;
        gameObject.SetActive(false);
    }

    public void ShowMetrics(MobileReceiverMetrics receiver)
    {
        currentReceiver = receiver;
        gameObject.SetActive(true);
    }
}
