using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class ThresholdSlider : MonoBehaviour, IPointerUpHandler
{
    public PrxVoxelChunkRenderer voxelRenderer;
    public TMP_Text thresholdValueText;

    private Slider thresholdSlider;

    void Awake()
    {
        thresholdSlider = GetComponent<Slider>();

        if (thresholdSlider != null)
        {
            thresholdSlider.onValueChanged.AddListener(OnSliderValueChanged);
        }
    }

    void Start()
    {
        if (thresholdSlider == null || voxelRenderer == null)
        {
            return;
        }

        // Copy the renderer threshold without invoking the slider event
        thresholdSlider.SetValueWithoutNotify(voxelRenderer.visibilityThreshold);

        // Show its equivalent value in dBm
        UpdateThresholdText(thresholdSlider.value);
    }

    private void OnSliderValueChanged(float value)
    {
        UpdateThresholdText(value);
    }

    public void OnPointerUp(PointerEventData eventData)
    {
        if (thresholdSlider == null || voxelRenderer == null)
        {
            return;
        }

        voxelRenderer.SetVisibilityThreshold(thresholdSlider.value);
    }

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