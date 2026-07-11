using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

/// <summary>
/// Controls the visible Prx threshold of the 3D heatmap renderer.
/// </summary>
public class ThresholdSlider : MonoBehaviour, IPointerUpHandler
{
    public PrxVoxelChunkRenderer voxelRenderer;
    public TMP_Text thresholdValueText;

    private Slider thresholdSlider;

    /// <summary>
    /// Caches the slider component and registers value updates.
    /// </summary>
    void Awake()
    {
        thresholdSlider = GetComponent<Slider>();

        if (thresholdSlider != null)
        {
            thresholdSlider.onValueChanged.AddListener(OnSliderValueChanged);
        }
    }

    /// <summary>
    /// Initializes the slider from the renderer threshold.
    /// </summary>
    void Start()
    {
        RefreshText();
    }

    /// <summary>
    /// Refreshes the visible threshold value after the renderer has valid Prx limits.
    /// </summary>
    public void RefreshText()
    {
        if (thresholdSlider == null)
        {
            thresholdSlider = GetComponent<Slider>();
        }

        if (thresholdSlider == null || voxelRenderer == null)
        {
            return;
        }

        // Copies the renderer threshold without invoking the slider event
        thresholdSlider.SetValueWithoutNotify(voxelRenderer.visibilityThreshold);

        // Shows its equivalent value in dBm when the renderer range is ready
        UpdateThresholdText(thresholdSlider.value);
    }

    /// <summary>
    /// Updates the threshold label while the slider moves.
    /// </summary>
    private void OnSliderValueChanged(float value)
    {
        UpdateThresholdText(value);
    }

    /// <summary>
    /// Rebuilds the voxel renderer after the user releases the slider.
    /// </summary>
    public void OnPointerUp(PointerEventData eventData)
    {
        if (thresholdSlider == null || voxelRenderer == null)
        {
            return;
        }

        voxelRenderer.SetVisibilityThreshold(thresholdSlider.value);
    }

    /// <summary>
    /// Converts the normalized threshold into dBm text.
    /// </summary>
    private void UpdateThresholdText(float normalizedThreshold)
    {
        if (thresholdValueText == null || voxelRenderer == null || !voxelRenderer.HasPrxRange)
        {
            return;
        }

        float thresholdDbm = Mathf.Lerp(
            voxelRenderer.MinPrx,
            voxelRenderer.MaxPrx,
            normalizedThreshold
        );

        thresholdValueText.text = $"{thresholdDbm:F2} dBm";
    }
}
