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

    /// <summary>
    /// Writes the static navigation hint.
    /// </summary>
    void Start()
    {
        instructionsText.text = "A / Left: previous    D / Right: next";
    }

    /// <summary>
    /// Refreshes the visible metrics while a receiver is selected.
    /// </summary>
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
            $"SNR: {m.snrDb:F2} dB";
    }

    /// <summary>
    /// Clears the selected receiver and hides the panel.
    /// </summary>
    public void HideMetrics()
    {
        currentReceiver = null;
        gameObject.SetActive(false);
    }

    /// <summary>
    /// Selects a receiver and shows its metrics panel.
    /// </summary>
    public void ShowMetrics(MobileReceiverMetrics receiver)
    {
        currentReceiver = receiver;
        gameObject.SetActive(true);
    }
}
