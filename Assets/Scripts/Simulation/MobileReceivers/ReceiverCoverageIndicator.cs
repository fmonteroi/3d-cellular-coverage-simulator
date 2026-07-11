using TMPro;
using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Displays the current coverage quality of a mobile receiver.
/// </summary>
public class ReceiverCoverageIndicator : MonoBehaviour
{
    [Header("References")]
    public MobileReceiverMetrics receiver;
    public Transform canvasTransform;
    public TMP_Text statusText;
    public Image statusDot;
    public SpriteRenderer groundIndicator;

    [Header("Colors")]
    public Color excellentColor = new Color32(35, 190, 90, 255);
    public Color goodColor = new Color32(245, 210, 40, 255);
    public Color fairColor = new Color32(255, 158, 0, 255);
    public Color noCoverageColor = new Color32(220, 55, 55, 255);
    public Color waitingColor = new Color32(150, 150, 150, 255);

    private Camera targetCamera;

    /// <summary>
    /// Finds the receiver reference and caches the main camera.
    /// </summary>
    void Awake()
    {
        // Finds the receiver on the parent object
        if (receiver == null)
        {
            receiver = GetComponentInParent<MobileReceiverMetrics>();
        }

        targetCamera = Camera.main;
    }

    /// <summary>
    /// Subscribes to receiver metric updates.
    /// </summary>
    void OnEnable()
    {
        if (receiver == null)
        {
            return;
        }

        // Listens for new receiver metrics
        receiver.OnMetricsUpdated += UpdateCoverage;

        if (receiver.hasValidMetrics)
        {
            UpdateCoverage(receiver.currentMetrics);
        }
        else
        {
            SetIndicator("Calculating...", waitingColor);
        }
    }

    /// <summary>
    /// Unsubscribes from receiver metric updates.
    /// </summary>
    void OnDisable()
    {
        if (receiver != null)
        {
            receiver.OnMetricsUpdated -= UpdateCoverage;
        }
    }

    /// <summary>
    /// Keeps the world space canvas facing the active camera.
    /// </summary>
    void LateUpdate()
    {
        if (targetCamera == null)
        {
            targetCamera = Camera.main;
        }

        if (targetCamera != null && canvasTransform != null)
        {
            // Keeps the message facing the camera
            canvasTransform.rotation = targetCamera.transform.rotation;
        }
    }

    /// <summary>
    /// Selects the coverage label and color from the current SNR value.
    /// </summary>
    private void UpdateCoverage(ReceiverMetricsSnapshot snapshot)
    {
        float snrDb = snapshot.snrDb;

        if (snrDb >= SimulationConfig.excellentSnrThresholdDb)
        {
            SetIndicator("Excellent coverage", excellentColor);
        }
        else if (snrDb >= SimulationConfig.goodSnrThresholdDb)
        {
            SetIndicator("Good coverage", goodColor);
        }
        else if (snrDb >= SimulationConfig.poorSnrThresholdDb)
        {
            SetIndicator("Fair coverage", fairColor);
        }
        else
        {
            SetIndicator("No coverage", noCoverageColor);
        }
    }

    /// <summary>
    /// Applies the selected coverage message and color to the UI elements.
    /// </summary>
    private void SetIndicator(string message, Color color)
    {
        if (statusText != null)
        {
            statusText.text = message;
        }

        if (statusDot != null)
        {
            statusDot.color = color;
        }

        if (groundIndicator != null)
        {
            groundIndicator.color = new Color(color.r, color.g, color.b, 0.3f);
        }
    }
}
